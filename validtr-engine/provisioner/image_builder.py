"""Docker image building and management."""

import logging

import docker

from executor.docker_util import get_docker_client

logger = logging.getLogger(__name__)


class ImageBuilder:
    """Builds and manages Docker images for validtr runs."""

    def __init__(self):
        self.client = get_docker_client()

    def build_agent_image(self, run_dir: str, run_id: str) -> str:
        """Build the agent container image. Returns image tag."""
        tag = f"validtr-agent-{run_id}"
        logger.info("Building agent image: %s", tag)

        try:
            self.client.images.build(
                path=run_dir,
                dockerfile="Dockerfile.agent",
                tag=tag,
                rm=True,
            )
        except docker.errors.BuildError as e:
            logger.error("Failed to build agent image: %s", e)
            raise

        return tag

    def build_test_runner_image(self, run_dir: str, run_id: str) -> str:
        """Build the test runner container image. Returns image tag."""
        tag = f"validtr-test-{run_id}"
        logger.info("Building test runner image: %s", tag)

        try:
            self.client.images.build(
                path=run_dir,
                dockerfile="Dockerfile.test-runner",
                tag=tag,
                rm=True,
            )
        except docker.errors.BuildError as e:
            logger.error("Failed to build test runner image: %s", e)
            raise

        return tag

    def cleanup(self, run_id: str) -> None:
        """Remove images for a given run."""
        for prefix in ["validtr-agent-", "validtr-test-"]:
            tag = f"{prefix}{run_id}"
            try:
                self.client.images.remove(tag, force=True)
                logger.info("Removed image: %s", tag)
            except docker.errors.ImageNotFound:
                pass
            except docker.errors.APIError as e:
                logger.warning("Failed to remove image %s: %s", tag, e)
