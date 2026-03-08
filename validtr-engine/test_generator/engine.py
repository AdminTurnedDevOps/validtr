"""Test Generator — generates and runs tests for execution output."""

import logging
import os
import re

import docker

from executor.docker_util import get_docker_client
from models.result import ExecutionResult
from models.task import TaskDefinition
from models.test_result import SingleTestResult, TestStatus, TestSuiteResult
from providers.base import LLMProvider, Message
from test_generator.prompts import TEST_GENERATION_SYSTEM, TEST_GENERATION_USER

logger = logging.getLogger(__name__)


class TestGenerator:
    """Generates tests from task spec + output artifacts, then runs them."""

    def __init__(self, provider: LLMProvider):
        self.provider = provider

    async def generate_and_run(
        self,
        task: TaskDefinition,
        execution: ExecutionResult,
    ) -> TestSuiteResult:
        """Generate tests and run them against the execution output."""
        logger.info("Generating tests for run %s", execution.run_id)

        # Generate test code
        test_code = await self._generate_tests(task, execution)

        # Write tests to workspace
        test_dir = os.path.join(execution.output_dir, "..", "tests")
        os.makedirs(test_dir, exist_ok=True)
        test_file = os.path.join(test_dir, "test_output.py")
        with open(test_file, "w") as f:
            f.write(test_code)

        logger.info("Generated test code (%d chars), running tests", len(test_code))

        # Run tests
        result = await self._run_tests(test_dir, execution.output_dir)
        result.test_code = test_code

        return result

    async def _generate_tests(
        self,
        task: TaskDefinition,
        execution: ExecutionResult,
    ) -> str:
        """Use LLM to generate test code."""
        # Prepare artifact info (never show agent reasoning, only outputs)
        artifact_names = "\n".join(f"- {name}" for name in execution.artifacts.keys())
        artifact_contents = ""
        for name, content in execution.artifacts.items():
            # Truncate very large files
            truncated = content[:3000] if len(content) > 3000 else content
            artifact_contents += f"\n--- {name} ---\n{truncated}\n"

        messages = [
            Message(role="system", content=TEST_GENERATION_SYSTEM),
            Message(
                role="user",
                content=TEST_GENERATION_USER.format(
                    task_description=task.raw_input,
                    success_criteria="\n".join(f"- {c}" for c in task.success_criteria),
                    testable_assertions="\n".join(f"- {a}" for a in task.testable_assertions),
                    artifact_names=artifact_names or "No artifacts",
                    artifact_contents=artifact_contents or "No content",
                ),
            ),
        ]

        response = await self.provider.complete(messages=messages, max_tokens=4096)

        # Clean up response — remove markdown fences if present
        code = response.content.strip()
        if code.startswith("```python"):
            code = code[9:]
        if code.startswith("```"):
            code = code[3:]
        if code.endswith("```"):
            code = code[:-3]

        return code.strip()

    async def _run_tests(self, test_dir: str, output_dir: str) -> TestSuiteResult:
        """Run tests in an isolated Docker container.

        Uses a pre-built image with test dependencies installed, then runs
        with network_mode=none so generated tests cannot make external calls.
        """
        try:
            client = get_docker_client()
        except docker.errors.DockerException as e:
            logger.error("Docker not available: %s", e)
            return TestSuiteResult(
                tests=[SingleTestResult(name="setup", status=TestStatus.ERROR, message=f"Docker not available: {e}")],
                total=1,
                errors=1,
                runner_output=f"Docker not available: {e}",
            )

        container = None
        try:
            # Ensure the test runner image exists (build once, reuse)
            image_tag = "validtr-test-runner:latest"
            self._ensure_test_runner_image(client, image_tag)

            logger.info("Running tests in isolated container")
            container = client.containers.run(
                image_tag,
                command=["python", "-m", "pytest", "/workspace/tests/",
                         "-v", "--tb=short", "--no-header", "-q"],
                volumes={
                    os.path.abspath(test_dir): {"bind": "/workspace/tests", "mode": "ro"},
                    os.path.abspath(output_dir): {"bind": "/workspace/output", "mode": "ro"},
                },
                environment={"VALIDTR_OUTPUT_DIR": "/workspace/output"},
                working_dir="/workspace/output",
                detach=True,
                network_mode="none",  # No network — tests must be self-contained
            )

            container.wait(timeout=120)
            output = container.logs(stdout=True, stderr=True).decode("utf-8", errors="replace")

            logger.debug("Test container output:\n%s", output[-2000:])
            return self._parse_pytest_output(output)

        except Exception as e:
            logger.error("Container test execution failed: %s", e)
            return TestSuiteResult(
                tests=[SingleTestResult(name="container", status=TestStatus.ERROR, message=str(e))],
                total=1,
                errors=1,
                runner_output=f"Container test execution failed: {e}",
            )
        finally:
            if container is not None:
                try:
                    container.remove(force=True)
                except Exception:
                    pass

    def _ensure_test_runner_image(self, client, tag: str) -> None:
        """Build the test runner image if it doesn't exist."""
        try:
            client.images.get(tag)
            return  # Already built
        except docker.errors.ImageNotFound:
            pass

        logger.info("Building test runner image: %s", tag)
        import io
        import tarfile

        dockerfile_content = b"""\
FROM python:3.12-slim
RUN pip install --no-cache-dir pytest pytest-asyncio httpx requests
WORKDIR /workspace
"""
        # Docker SDK requires a tar archive as build context
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w") as tar:
            info = tarfile.TarInfo(name="Dockerfile")
            info.size = len(dockerfile_content)
            tar.addfile(info, io.BytesIO(dockerfile_content))
        buf.seek(0)

        client.images.build(
            fileobj=buf,
            custom_context=True,
            tag=tag,
            rm=True,
        )

    def _parse_pytest_output(self, output: str) -> TestSuiteResult:
        """Parse pytest verbose output into a TestSuiteResult."""
        tests = []
        lines = output.split("\n")

        for line in lines:
            # Match pytest verbose output: "test_name PASSED" or "test_name FAILED"
            match = re.match(r"^(.+?)\s+(PASSED|FAILED|ERROR|SKIPPED)", line.strip())
            if match:
                name = match.group(1).strip()
                status_str = match.group(2)
                status_map = {
                    "PASSED": TestStatus.PASSED,
                    "FAILED": TestStatus.FAILED,
                    "ERROR": TestStatus.ERROR,
                    "SKIPPED": TestStatus.SKIPPED,
                }
                tests.append(SingleTestResult(
                    name=name,
                    status=status_map.get(status_str, TestStatus.ERROR),
                ))

        passed = sum(1 for t in tests if t.status == TestStatus.PASSED)
        failed = sum(1 for t in tests if t.status == TestStatus.FAILED)
        errors = sum(1 for t in tests if t.status == TestStatus.ERROR)
        skipped = sum(1 for t in tests if t.status == TestStatus.SKIPPED)

        return TestSuiteResult(
            tests=tests,
            total=len(tests),
            passed=passed,
            failed=failed,
            errors=errors,
            skipped=skipped,
            runner_output=output,
        )
