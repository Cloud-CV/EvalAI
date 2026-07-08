#!/usr/bin/env bash
set -euo pipefail

if command -v docker >/dev/null 2>&1; then
  echo "Docker is already installed."
else
  echo "Installing Docker for Cloud Agent VM..."
  sudo apt-get update
  sudo apt-get install -y fuse-overlayfs iptables docker.io docker-compose-plugin

  sudo update-alternatives --set iptables /usr/sbin/iptables-legacy
  sudo update-alternatives --set ip6tables /usr/sbin/ip6tables-legacy

  sudo mkdir -p /etc/docker
  if [ ! -f /etc/docker/daemon.json ]; then
    sudo tee /etc/docker/daemon.json >/dev/null <<'EOF'
{
  "storage-driver": "fuse-overlayfs",
  "cgroup-parent": "system.slice"
}
EOF
  fi

  sudo systemctl enable --now docker
  sudo usermod -aG docker "${USER}" || true
fi

docker --version
docker compose version
