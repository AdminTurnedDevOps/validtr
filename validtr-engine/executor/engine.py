"""Execution Engine — runs tasks inside Docker containers."""

import json
import logging
import os
import time

import docker

from executor.docker_util import BASE_AGENT_IMAGE, ensure_base_images, get_docker_client
from executor.safety import SafetyLimits
from executor.trace import TraceCollector
from models.result import ExecutionResult
from models.stack import MCPTransport, StackRecommendation
from models.task import TaskDefinition
from provisioner.compose_generator import ComposeGenerator
from provisioner.credentials import resolve_credentials

logger = logging.getLogger(__name__)


class ExecutionEngine:
    """Runs a task in a provisioned Docker environment and captures results."""

    def __init__(
        self,
        safety_limits: SafetyLimits | None = None,
        output_base: str | None = None,
    ):
        self.safety = safety_limits or SafetyLimits()
        self.compose_gen = ComposeGenerator(output_base=output_base)
        self.docker_client = get_docker_client()
        ensure_base_images(self.docker_client)

    async def execute(
        self,
        run_id: str,
        task: TaskDefinition,
        stack: StackRecommendation,
        api_keys: dict[str, str] | None = None,
    ) -> ExecutionResult:
        """Execute a task in a Docker container."""
        trace = TraceCollector()
        logger.info("Starting execution for run %s", run_id)

        try:
            # Resolve credentials
            credentials = resolve_credentials(stack, api_keys)

            # Generate Docker Compose config and supporting files
            run_dir, compose_path = self.compose_gen.generate(run_id, stack, credentials)

            # Write task and stack definitions to workspace
            workspace_dir = os.path.join(run_dir, "workspace")
            with open(os.path.join(workspace_dir, "task.json"), "w") as f:
                json.dump(task.model_dump(), f, indent=2)
            with open(os.path.join(workspace_dir, "stack.json"), "w") as f:
                json.dump(stack.model_dump(), f, indent=2)

            # Determine if we need a per-run image (MCP servers) or can use the base
            has_mcp = any(
                s.transport == MCPTransport.STDIO for s in stack.mcp_servers
            )
            image_tag = self._resolve_agent_image(run_dir, run_id, has_mcp)

            # Build and run agent container
            artifacts = await self._run_agent_container(
                run_dir, run_id, image_tag, credentials, stack, trace
            )

            execution_trace = trace.finalize()

            return ExecutionResult(
                run_id=run_id,
                artifacts=artifacts,
                trace=execution_trace,
                output_dir=os.path.join(workspace_dir, "output"),
                success=True,
            )

        except Exception as e:
            logger.error("Execution failed for run %s: %s", run_id, e)
            execution_trace = trace.finalize()
            execution_trace.error = str(e)
            return ExecutionResult(
                run_id=run_id,
                trace=execution_trace,
                success=False,
                error=str(e),
            )

    def _resolve_agent_image(self, run_dir: str, run_id: str, has_mcp: bool) -> str:
        """Return the image tag to use. Builds a per-run image only if MCP servers need installing."""
        if not has_mcp:
            return BASE_AGENT_IMAGE

        tag = f"validtr-agent-{run_id}"
        logger.info("Building per-run agent image for MCP servers: %s", tag)
        try:
            self.docker_client.images.build(
                path=run_dir,
                dockerfile="Dockerfile.agent",
                tag=tag,
                rm=True,
            )
        except docker.errors.BuildError as e:
            raise RuntimeError(f"Failed to build agent image: {e}") from e
        return tag

    async def _run_agent_container(
        self,
        run_dir: str,
        run_id: str,
        image_tag: str,
        credentials: dict[str, str],
        stack: StackRecommendation,
        trace: TraceCollector,
    ) -> dict[str, str]:
        """Run the agent container. Returns artifacts dict."""
        start = time.time()

        workspace_dir = os.path.join(run_dir, "workspace")
        entrypoint_path = os.path.join(run_dir, "entrypoint.py")
        agent_loop_path = os.path.join(run_dir, "agent_loop.py")

        environment = {
            "VALIDTR_RUN_ID": run_id,
            "VALIDTR_PROVIDER": stack.llm.provider,
            "VALIDTR_MODEL": stack.llm.model,
        }
        environment.update(credentials)

        volumes = {
            workspace_dir: {"bind": "/workspace", "mode": "rw"},
            entrypoint_path: {"bind": "/app/entrypoint.py", "mode": "ro"},
            agent_loop_path: {"bind": "/app/agent_loop.py", "mode": "ro"},
        }

        logger.info("Running agent container (image: %s)", image_tag)
        container = None
        try:
            container = self.docker_client.containers.run(
                image_tag,
                detach=True,
                volumes=volumes,
                environment=environment,
            )

            result = container.wait(timeout=self.safety.timeout_seconds)
            logs = container.logs(stdout=True, stderr=True).decode("utf-8", errors="replace")
            logger.info("Agent container finished with status %s", result.get("StatusCode", -1))
            logger.debug("Container logs:\n%s", logs[-2000:])

        except Exception as e:
            logger.error("Container execution failed: %s", e)
            raise
        finally:
            if container is not None:
                try:
                    container.remove(force=True)
                except Exception:
                    pass

        duration_ms = int((time.time() - start) * 1000)
        trace.record_llm_call(
            provider="docker",
            model=image_tag,
            input_tokens=0,
            output_tokens=0,
            duration_ms=duration_ms,
        )

        # Collect artifacts from output directory
        artifacts = {}
        output_dir = os.path.join(workspace_dir, "output")
        if os.path.exists(output_dir):
            for root, _dirs, files in os.walk(output_dir):
                for filename in files:
                    filepath = os.path.join(root, filename)
                    rel_path = os.path.relpath(filepath, output_dir)
                    try:
                        with open(filepath) as f:
                            artifacts[rel_path] = f.read()
                    except (UnicodeDecodeError, OSError):
                        artifacts[rel_path] = "<binary file>"

        logger.info("Collected %d artifacts", len(artifacts))
        return artifacts

    async def cleanup(self, run_id: str) -> None:
        """Clean up Docker resources for a run."""
        tag = f"validtr-agent-{run_id}"
        try:
            self.docker_client.images.remove(tag, force=True)
        except docker.errors.ImageNotFound:
            pass
        except docker.errors.APIError as e:
            logger.warning("Cleanup failed for %s: %s", tag, e)
