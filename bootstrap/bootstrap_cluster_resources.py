#!/usr/bin/env python3
import os
import subprocess
import sys
from dotenv import load_dotenv

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
SERVICES_DIR = os.path.join(PROJECT_ROOT, "services")
DEPLOY_DIR = os.path.join(PROJECT_ROOT, "deploy")
ENV_FILE = os.path.join(PROJECT_ROOT, ".env")

IMAGE_MAPPING = {
    "agent": "armada-agent",
    "backend": "armada-backend",
    "fingerprint-provider": "armada-fingerprint-provider",
    "frontend": "armada-frontend",
    "orchestrator": "armada-orchestrator",
    "proxy-provider": "armada-proxy-provider",
}


def run(cmd, cwd=None):
    print(f"\n>>> {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd)
    if result.returncode != 0:
        print(f"Command failed with exit code {result.returncode}")
        sys.exit(1)


def get_docker_username():
    load_dotenv(ENV_FILE)
    username = os.getenv("DOCKER_HUB_USERNAME")
    if not username:
        print(f"Error: DOCKER_HUB_USERNAME not found in {ENV_FILE}")
        sys.exit(1)
    return username


def print_summary(mode, username=None):
    print("\n" + "=" * 50)
    print("  INSTALLATION COMPLETE")
    print("=" * 50)
    if mode == "public":
        print("\nWhat was done:")
        print("  - Helm release 'armada' installed with public images (armadasvc)")
    elif mode == "minikube":
        print(f"\nWhat was done:")
        print(f"  - 6 Docker images built inside Minikube ({username})")
        print(f"  - Helm release 'armada' installed with local images ({username})")
    else:
        print(f"\nWhat was done:")
        print(f"  - 6 Docker images built and pushed to DockerHub ({username})")
        print(f"  - Helm release 'armada' installed with private images ({username})")
    print("\nTo check deployed resources:")
    print("  kubectl get deploy -A | grep armada")
    print("\nTo uninstall:")
    print("  helm uninstall armada")
    print("\n" + "=" * 50)
    input("\nPress Enter to exit...")


def install_public():
    print("\n== Installing with public images (armadasvc) ==\n")
    run("helm install armada . --set dockerHubName=armadasvc --set distrib=kube", cwd=DEPLOY_DIR)
    print_summary("public")


def install_private():
    username = get_docker_username()
    print(f"\n== Building & pushing with DockerHub user: {username} ==\n")

    for folder, image_name in IMAGE_MAPPING.items():
        full_image = f"{username}/{image_name}"
        build_ctx = os.path.join(SERVICES_DIR, folder)

        if not os.path.isdir(build_ctx):
            print(f"Warning: {build_ctx} does not exist, skipping.")
            continue

        run(f"docker build -t {full_image} .", cwd=build_ctx)
        run(f"docker push {full_image}")

    print(f"\n== Installing with private images ({username}) ==\n")
    run(
        f"helm install armada . "
        f"--set dockerHubName={username} "
        f"--set imagePullSecrets[0].name=armada-docker-registry-secret "
        f"--set distrib=kube",
        cwd=DEPLOY_DIR,
    )
    print_summary("private", username)


def install_minikube():
    username = get_docker_username()
    print(f"\n== [DEV AND QUICK-START MODE] Building images inside Minikube ({username}) ==\n")

    for folder, image_name in IMAGE_MAPPING.items():
        full_image = f"{username}/{image_name}"
        build_ctx = os.path.join(SERVICES_DIR, folder)

        if not os.path.isdir(build_ctx):
            print(f"Warning: {build_ctx} does not exist, skipping.")
            continue

        run(f"eval $(minikube docker-env) && docker build -t {full_image} .", cwd=build_ctx)

    print(f"\n== Installing with local Minikube images ({username}) ==\n")
    run(
        f"helm install armada . "
        f"--set dockerHubName={username} "
        f"--set imagePullPolicy=Never "
        f"--set distrib=minikube",
        cwd=DEPLOY_DIR,
    )
    print_summary("minikube", username)


def main():
    print("Bootstrap cluster resources")
    print("---------------------------")
    print("1. Install using public images (armadasvc)")
    print("2. Build, push & install using private DockerHub registry")
    print("3. [FIRST TRY OR DEV MODE] Minikube")
    print()

    choice = input("Choose an option (1/2/3): ").strip()

    if choice == "1":
        install_public()
    elif choice == "2":
        install_private()
    elif choice == "3":
        install_minikube()
    else:
        print("Invalid choice.")
        sys.exit(1)


if __name__ == "__main__":
    main()
