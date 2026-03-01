#!/usr/bin/env python3
"""
Bootstrap Kubernetes secrets from .env file.
Uses the official Kubernetes Python client to create/update secrets.

Usage:
    pip install kubernetes python-dotenv
    python bootstrap_secrets.py [--namespace default]
"""

import argparse
import base64
import json
import sys
from pathlib import Path

from dotenv import dotenv_values
from kubernetes import client, config


def load_env(env_path: Path) -> dict[str, str]:
    return dotenv_values(env_path)


def check_keys(env: dict, keys: list[str]) -> list[str]:
    """Return list of missing keys."""
    return [k for k in keys if not env.get(k)]


def apply_secret(v1: client.CoreV1Api, secret: client.V1Secret):
    name = secret.metadata.name
    ns = secret.metadata.namespace
    try:
        v1.read_namespaced_secret(name, ns)
        v1.replace_namespaced_secret(name, ns, secret)
        print(f"    {name} updated")
    except client.ApiException as e:
        if e.status == 404:
            v1.create_namespaced_secret(ns, secret)
            print(f"    {name} created")
        else:
            raise


def build_docker_creds_secret(env: dict, ns: str) -> client.V1Secret:
    return client.V1Secret(
        api_version="v1",
        kind="Secret",
        metadata=client.V1ObjectMeta(name="armada-docker-username-secret", namespace=ns),
        type="Opaque",
        string_data={"username": env["DOCKER_HUB_USERNAME"]},
    )


def build_docker_registry_secret(env: dict, ns: str) -> client.V1Secret:
    docker_config = {
        "auths": {
            "https://index.docker.io/v1/": {
                "username": env["DOCKER_HUB_USERNAME"],
                "password": env["DOCKER_HUB_PASSWORD"],
                "email": env["DOCKER_HUB_MAIL"],
                "auth": base64.b64encode(
                    f"{env['DOCKER_HUB_USERNAME']}:{env['DOCKER_HUB_PASSWORD']}".encode()
                ).decode(),
            }
        }
    }
    return client.V1Secret(
        api_version="v1",
        kind="Secret",
        metadata=client.V1ObjectMeta(name="armada-docker-registry-secret", namespace=ns),
        type="kubernetes.io/dockerconfigjson",
        string_data={".dockerconfigjson": json.dumps(docker_config)},
    )


def build_ipqs_secret(env: dict, ns: str) -> client.V1Secret:
    return client.V1Secret(
        api_version="v1",
        kind="Secret",
        metadata=client.V1ObjectMeta(name="armada-ipqs-secret", namespace=ns),
        type="Opaque",
        string_data={"IPQS_KEY": env["IPQS_KEY"]},
    )


def build_sql_server_secret(env: dict, ns: str) -> client.V1Secret:
    return client.V1Secret(
        api_version="v1",
        kind="Secret",
        metadata=client.V1ObjectMeta(name="armada-sql-server-secret", namespace=ns),
        type="Opaque",
        string_data={
            "SQL_SERVER_USER": env["SQL_SERVER_USER"],
            "SQL_SERVER_PASSWORD": env["SQL_SERVER_PASSWORD"],
            "SQL_SERVER_DB": env["SQL_SERVER_DB"],
            "SQL_SERVER_NAME": env["SQL_SERVER_NAME"],
        },
    )


def main():
    parser = argparse.ArgumentParser(description="Bootstrap K8s secrets from .env")
    parser.add_argument("--namespace", default="default")
    parser.add_argument(
        "--env-file",
        default=str(Path(__file__).resolve().parent.parent / ".env"),
    )
    args = parser.parse_args()

    env_path = Path(args.env_file)
    if not env_path.exists():
        sys.exit(f".env not found: {env_path}")

    env = load_env(env_path)
    config.load_kube_config()
    v1 = client.CoreV1Api()

    ns = args.namespace
    print(f"==> Bootstrapping secrets in namespace: {ns}")

    builders = [
        (build_docker_creds_secret, ["DOCKER_HUB_USERNAME"]),
        (build_docker_registry_secret, ["DOCKER_HUB_USERNAME", "DOCKER_HUB_PASSWORD", "DOCKER_HUB_MAIL"]),
        (build_ipqs_secret, ["IPQS_KEY"]),
        (build_sql_server_secret, ["SQL_SERVER_USER", "SQL_SERVER_PASSWORD", "SQL_SERVER_DB", "SQL_SERVER_NAME"]),
    ]

    skipped = 0
    for build, required_keys in builders:
        missing = check_keys(env, required_keys)
        if missing:
            print(f"    SKIPPED {build.__name__}: missing {', '.join(missing)}")
            skipped += 1
            continue
        apply_secret(v1, build(env, ns))

    total = len(builders)
    applied = total - skipped
    print(f"==> Done: {applied}/{total} secrets applied, {skipped} skipped.")


if __name__ == "__main__":
    main()
