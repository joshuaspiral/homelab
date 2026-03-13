# Homelab Configuration Files
This is for my Homelab setup.

**theseus** is the main node (Lenovo M720q, 1TB NVMe) running Proxmox with 5 LXCs.
**hyperion** is a Fedora Workstation GPU machine on the desk — only on when needed for OCR or LLM stuff.

# **theseus** 
## LXCs
- lxc-infra (101): Cloudflared, Homepage, Uptime Kuma
- lxc-productivity (102): Paperless-ngx, Vaultwarden, CouchDB (for Obsidian LiveSync), Actual Budget, it-tools
- lxc-photos (103): Immich (iGPU passthrough)
- lxc-media (104): Jellyfin, Navidrome, arr-stack, qBittorrent + Gluetun
- lxc-misc (105): Ephemeral/experimental services, demo apps, etc.

## Storage Layout
ZFS:
```
/mnt/data/
├── photos/     → bind mount → lxc-photos       (/mnt/photos)
├── media/      → bind mount → lxc-media        (/mnt/media)
├── music/      → bind mount → lxc-media        (/mnt/music)
├── downloads/  → bind mount → lxc-media        (/mnt/downloads)
├── documents/  → bind mount → lxc-productivity (/mnt/documents)
└── files/      → host only  → cold storage
```

# Cool Stuff I've Set Up for this Homelab
Read more on [my homelab weblog](https://joshuaspiral.xyz/homelab)!

# todo
- [ ] update docker compose files to follow most recent documentation convention and versions
