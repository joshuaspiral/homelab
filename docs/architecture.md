# Homelab Architecture

# Nodes

## theseus (Primary — Lenovo M720q)
- Proxmox VE
- Intel i5-8500T
- 16GB DDR4 RAM
- 512GB M.2 NVMe (ADATA SX8200PNP)

## ...
- Fedora Workstation
- AMD Ryzen 5 3600
- NVIDIA RTX 2060 Super (8GB VRAM)
- 16GB DDR4 RAM
- 1TB M.2 NVMe
- Runs Ollama locally for LLM inference + Open WebUI backend

## zenith (ASUS Zenbook UX3405)
- Arch Linux + dwm
- 32GB RAM
- 1TB M.2 NVMe

# Proxmox (theseus)

## Container Overview
```
theseus (Proxmox)
├── lxc-infra         (10.0.0.201) # Caddy, WireGuard, Authentik, Pihole
│                                  # 1.5GB RAM, 1vCPU, 20GB disk
├── lxc-productivity  (10.0.0.202) # Paperless-ngx, Vaultwarden, CouchDB, Open WebUI
│                                  # 2.5GB RAM, 2vCPU, 40GB disk
│                                  # /mnt/documents bind mount
├── lxc-photos        (10.0.0.203) # Immich + iGPU passthrough
│                                  # 3GB RAM, 2vCPU, 30GB disk
│                                  # /mnt/photos bind mount
├── lxc-media         (10.0.0.204) # Jellyfin, Navidrome, Sonarr, Radarr, Lidarr
│                                  # Readarr, Prowlarr, qBittorrent + iGPU passthrough
│                                  # 3GB RAM, 3vCPU, 30GB disk
│                                  # /mnt/media bind mount
├── lxc-storage       (10.0.0.205) # Filebrowser, Beets, slskd
│                                  # 512MB RAM, 1vCPU, 20GB disk
│                                  # /mnt/music and /mnt/files bind mounts
└── lxc-homeauto      (10.0.0.206) # Home Assistant
                                   # 1GB RAM, 1vCPU, 20GB disk
```

## Host Storage Layout
```
/mnt/data/
├── photos/     → bind mount → lxc-photos
├── media/      → bind mount → lxc-media
├── music/      → bind mount → lxc-storage
├── documents/  → bind mount → lxc-productivity
└── files/      → bind mount → lxc-storage
```

# Document Pipeline
ADF → Chandra (OCR via Ollama on arch-desktop) → Paperless-ngx (lxc-productivity)

# Network Topology
All containers on a single Proxmox Linux bridge (vmbr0), 10.0.0.0/24.
Static IPs assigned via Proxmox container config.
External access via Cloudflare Tunnel (terminating on lxc-infra).
Remote access via Tailscale on all nodes.
