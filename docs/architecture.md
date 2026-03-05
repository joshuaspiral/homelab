# Architecture of my Homelab

# Node(s)
## Primary
M720q:
- Proxmox
- i5-8500T @ ? GHz
- 16GB DDR4 RAM
- 1TB M.2 NVME
## Desktop
- Arch Linux
- Ryzen 5 3600
- RTX 2060 Super, 8GB VRAM
- 16GB DDR4 RAM
# Proxmox
## Overview
```
Proxmox (M720q)
├── lxc-media         # Jellyfin, Navidrome, Sonarr, Radarr, Lidarr, Readarr
│                     # Prowlarr, qBittorrent + iGPU passthrough
│                     # 3GB RAM, 3vCPU, 30GB disk
│                     # /mnt/media bind mount for all media files
├── lxc-photos        # Immich + iGPU passthrough
│                     # 3GB RAM, 2vCPU, 30GB disk
│                     # /mnt/photos bind mount
├── lxc-productivity  # Paperless-ngx, Vaultwarden, Obsidian/CouchDB, Open Web UI
│                     # 2.5GB RAM, 2vCPU, 40GB disk
│                     # /mnt/documents bind mount
├── lxc-storage       # Filebrowser, Beets, slskd
│                     # 512MB RAM, 1vCPU, 20GB disk
│                     # /mnt/music and /mnt/files bind mounts
├── lxc-infra         # Caddy, WireGuard, Authentik, Pihole
│                     # 1.5GB RAM, 1vCPU, 20GB disk
└── lxc-homeauto      # Home Assistant
                      # 1GB RAM, 1vCPU, 20GB disk

Separate physical machine:
└── arch-desktop      # Ollama (Chandra inference + LLMs for Open Web UI), gaming
                      # On same LAN, accessed via static IP
```

# Network Topology
All containers run on a single Proxmox Linux bridge (vmbr0) in the 
192.168.x.0/24 range, assigned static IPs via the Proxmox container 
configuration. 
