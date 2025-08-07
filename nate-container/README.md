# Nate's Docker Development Container

A fully configured Ubuntu development container with GPU support, SSH access, and FRP integration.

## Specifications

- **OS**: Ubuntu 22.04 LTS
- **Resources**: 4 CPU cores, 8GB RAM, 120GB persistent storage
- **GPU**: NVIDIA RTX 4090 with CUDA 12.8 support
- **User**: `nate` with sudo privileges
- **SSH**: Accessible via FRP tunnel on port 2244

## Quick Start

```bash
# Navigate to container directory
cd /home/gaen/agents_gaen/nate-container

# Run setup script (builds and starts container)
./setup.sh
```

## Manual Commands

```bash
# Build container
docker compose build

# Start container
docker compose up -d

# Stop container
docker compose down

# View logs
docker compose logs -f

# Shell access (local)
docker exec -it nate-dev-container bash

# SSH access (local)
ssh nate@localhost -p 2244

# SSH access (remote via FRP)
ssh nate@106.14.213.46 -p 2244
```

## Connection Details

- **Local SSH**: `ssh nate@localhost -p 2244`
- **Remote SSH**: `ssh nate@106.14.213.46 -p 2244`
- **Username**: `nate`
- **Password**: `nate123`
- **Sudo**: Password-less sudo enabled

## Storage

- **Data Volume**: `/home/nate/data` → `/home/gaen/nate-container-data`
- **Projects Volume**: `/home/nate/projects` → `/home/gaen/nate-container-projects`

Both volumes are persistent and survive container restarts.

## GPU Support

The container has full access to the NVIDIA RTX 4090 GPU with CUDA 12.8 toolkit installed.

Test GPU access:
```bash
# Inside container
nvidia-smi
nvcc --version
```

## FRP Configuration

The container SSH is automatically exposed via FRP tunnel:
- **Local Port**: 2244
- **Remote Port**: 2244 (via 106.14.213.46)
- **FRP Service**: Managed by systemd on host

## Security Notes

- Container runs with additional capabilities for development
- SSH password authentication is enabled (consider using SSH keys for production)
- User `nate` has password-less sudo access
- GPU access requires proper NVIDIA driver installation on host

## Troubleshooting

### Container won't start
```bash
docker compose logs
```

### GPU not accessible
```bash
# Check NVIDIA runtime
docker info | grep nvidia

# Test GPU in container
docker exec nate-dev-container nvidia-smi
```

### SSH connection fails
```bash
# Check container is running
docker ps | grep nate-dev-container

# Check FRP service
systemctl status frpc

# Check port mapping
netstat -tlnp | grep 2244
```

### Storage issues
```bash
# Check volume mounts
docker inspect nate-dev-container | grep -A 10 "Mounts"

# Check host directories
ls -la /home/gaen/nate-container-*
```

## Container Management

### Restart container
```bash
docker compose restart
```

### Update container
```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Clean up
```bash
# Stop and remove container
docker compose down

# Remove image
docker rmi nate-container_nate-container

# Clean up volumes (⚠️  This will delete all data)
sudo rm -rf /home/gaen/nate-container-data /home/gaen/nate-container-projects
```