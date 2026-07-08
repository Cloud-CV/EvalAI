#!/usr/bin/env bash
set -euo pipefail

ensure_docker_compose_package() {
  if apt-cache show docker-compose-plugin >/dev/null 2>&1; then
    echo "docker-compose-plugin"
    return 0
  fi
  if apt-cache show docker-compose-v2 >/dev/null 2>&1; then
    echo "docker-compose-v2"
    return 0
  fi
  echo "No docker compose package found in apt repositories." >&2
  return 1
}

configure_iptables_legacy_if_available() {
  if update-alternatives --list iptables 2>/dev/null | grep -q legacy; then
    sudo update-alternatives --set iptables /usr/sbin/iptables-legacy
  else
    echo "Skipping iptables-legacy setup (not available on this image)."
  fi

  if update-alternatives --list ip6tables 2>/dev/null | grep -q legacy; then
    sudo update-alternatives --set ip6tables /usr/sbin/ip6tables-legacy
  else
    echo "Skipping ip6tables-legacy setup (not available on this image)."
  fi
}

configure_docker_daemon() {
  sudo mkdir -p /etc/docker
  if [ ! -f /etc/docker/daemon.json ]; then
    sudo tee /etc/docker/daemon.json >/dev/null <<'EOF'
{
  "storage-driver": "fuse-overlayfs",
  "cgroup-parent": "system.slice"
}
EOF
  fi
}

start_docker_daemon() {
  local dockerd_log
  dockerd_log="$(mktemp)"

  if sudo docker info >/dev/null 2>&1; then
    echo "Docker daemon is already running."
    rm -f "${dockerd_log}"
    return 0
  fi

  if command -v systemctl >/dev/null 2>&1 && [ -d /run/systemd/system ]; then
    if sudo systemctl enable --now docker 2>/dev/null; then
      rm -f "${dockerd_log}"
      return 0
    fi
    echo "systemctl could not start docker; falling back to dockerd."
  fi

  if ! pgrep -x dockerd >/dev/null 2>&1; then
    echo "Starting dockerd in the background..."
    sudo dockerd >"${dockerd_log}" 2>&1 &
  fi

  for _ in $(seq 1 30); do
    if sudo docker info >/dev/null 2>&1; then
      rm -f "${dockerd_log}"
      return 0
    fi
    sleep 1
  done

  echo "Docker daemon failed to start. Recent dockerd logs:" >&2
  tail -50 "${dockerd_log}" >&2 || true
  rm -f "${dockerd_log}"
  return 1
}

if command -v docker >/dev/null 2>&1; then
  echo "Docker client is already installed."
else
  echo "Installing Docker for Cloud Agent VM..."
  if ! compose_package="$(ensure_docker_compose_package)"; then
    echo "Cannot install Docker without a compose package." >&2
    exit 1
  fi
  sudo apt-get update
  sudo apt-get install -y fuse-overlayfs iptables docker.io "${compose_package}"
  configure_iptables_legacy_if_available
  configure_docker_daemon
  if getent group docker >/dev/null 2>&1; then
    sudo usermod -aG docker "${USER}" || true
  fi
fi

start_docker_daemon

sudo docker --version
sudo docker compose version
