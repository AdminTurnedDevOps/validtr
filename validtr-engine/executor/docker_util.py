"""Docker client helper — handles non-standard socket paths (Docker Desktop)."""

import io
import logging
import os
import tarfile

import docker

logger = logging.getLogger(__name__)

BASE_AGENT_IMAGE = "validtr-agent-base:latest"
BASE_TEST_RUNNER_IMAGE = "validtr-test-runner:latest"


def get_docker_client(**kwargs) -> docker.DockerClient:
    """Create a Docker client, auto-detecting Docker Desktop socket if needed."""
    # If DOCKER_HOST is already set, docker.from_env() will use it.
    # Otherwise, check for Docker Desktop's socket location on macOS.
    if not os.environ.get("DOCKER_HOST"):
        desktop_sock = os.path.expanduser("~/.docker/run/docker.sock")
        if os.path.exists(desktop_sock):
            return docker.DockerClient(base_url=f"unix://{desktop_sock}", **kwargs)

    return docker.from_env(**kwargs)


def ensure_base_images(client: docker.DockerClient) -> None:
    """Build base images if they don't already exist."""
    _ensure_agent_base(client)
    _ensure_test_runner_base(client)


def _image_exists(client: docker.DockerClient, tag: str) -> bool:
    try:
        client.images.get(tag)
        return True
    except docker.errors.ImageNotFound:
        return False


def _ensure_agent_base(client: docker.DockerClient) -> None:
    if _image_exists(client, BASE_AGENT_IMAGE):
        return

    logger.info("Building base agent image (one-time): %s", BASE_AGENT_IMAGE)
    template_path = os.path.join(
        os.path.dirname(__file__), "..", "provisioner", "templates", "agent-base.Dockerfile"
    )
    with open(template_path) as f:
        dockerfile_content = f.read().encode()

    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        info = tarfile.TarInfo(name="Dockerfile")
        info.size = len(dockerfile_content)
        tar.addfile(info, io.BytesIO(dockerfile_content))
    buf.seek(0)

    client.images.build(fileobj=buf, custom_context=True, tag=BASE_AGENT_IMAGE, rm=True)
    logger.info("Base agent image built: %s", BASE_AGENT_IMAGE)


def _ensure_test_runner_base(client: docker.DockerClient) -> None:
    if _image_exists(client, BASE_TEST_RUNNER_IMAGE):
        return

    logger.info("Building base test runner image (one-time): %s", BASE_TEST_RUNNER_IMAGE)
    template_path = os.path.join(
        os.path.dirname(__file__), "..", "provisioner", "templates", "test-runner.Dockerfile"
    )
    with open(template_path) as f:
        dockerfile_content = f.read().encode()

    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        info = tarfile.TarInfo(name="Dockerfile")
        info.size = len(dockerfile_content)
        tar.addfile(info, io.BytesIO(dockerfile_content))
    buf.seek(0)

    client.images.build(fileobj=buf, custom_context=True, tag=BASE_TEST_RUNNER_IMAGE, rm=True)
    logger.info("Base test runner image built: %s", BASE_TEST_RUNNER_IMAGE)
