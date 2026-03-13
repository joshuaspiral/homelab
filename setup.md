Documentation for myself on setup !

# theseus

## Proxmox Install

During install, selected `local-zfs` as the disk target. This creates a ZFS pool called `rpool` automatically on the NVMe, with the OS on `rpool/ROOT/pve-1` and a separate dataset for VM/LXC storage.

After install:
```bash
# Upgrade pool feature flags (safe, one-way)
zpool upgrade rpool

# Enable LZ4 compression on all data
zfs set compression=lz4 rpool/data
```

## ZFS Data Layout

Each data type gets its own ZFS dataset so they can be snapshotted and configured independently.

```bash
zfs create rpool/data
zfs create rpool/data/photos
zfs create rpool/data/media
zfs create rpool/data/music
zfs create rpool/data/downloads
zfs create rpool/data/documents
zfs create rpool/data/files
```

These automatically mount at `/mnt/data/*` via ZFS mountpoints. Check with `zfs list`.

## LXCs

Download the Debian 12 template first:
```bash
# Get latest available template
pveam update
pveam available --section system | grep debian
# Copy the latest debian-12-* line and use that in pct create

pveam download local debian-12-standard_12.12-1_amd64.tar.zst
```

Create all containers:
```bash
pct create 101 local:vztmpl/debian-12-standard_12.12-1_amd64.tar.zst \
  --hostname lxc-infra --cores 1 --memory 1024 --swap 512 \
  --rootfs local-zfs:20 \
  --net0 name=eth0,bridge=vmbr0,gw=10.0.0.1,ip=10.0.0.101/24 \
  --unprivileged 1

pct create 102 local:vztmpl/debian-12-standard_12.12-1_amd64.tar.zst \
  --hostname lxc-productivity --cores 2 --memory 2560 --swap 512 \
  --rootfs local-zfs:40 \
  --net0 name=eth0,bridge=vmbr0,gw=10.0.0.1,ip=10.0.0.102/24 \
  --unprivileged 1

pct create 103 local:vztmpl/debian-12-standard_12.12-1_amd64.tar.zst \
  --hostname lxc-photos --cores 2 --memory 6144 --swap 512 \
  --rootfs local-zfs:30 \
  --net0 name=eth0,bridge=vmbr0,gw=10.0.0.1,ip=10.0.0.103/24 \
  --unprivileged 1

pct create 104 local:vztmpl/debian-12-standard_12.12-1_amd64.tar.zst \
  --hostname lxc-media --cores 3 --memory 3072 --swap 512 \
  --rootfs local-zfs:30 \
  --net0 name=eth0,bridge=vmbr0,gw=10.0.0.1,ip=10.0.0.104/24 \
  --unprivileged 1

pct create 105 local:vztmpl/debian-12-standard_12.12-1_amd64.tar.zst \
  --hostname lxc-misc --cores 1 --memory 512 --swap 512 \
  --rootfs local-zfs:10 \
  --net0 name=eth0,bridge=vmbr0,gw=10.0.0.1,ip=10.0.0.105/24 \
  --unprivileged 1
```

Enable nesting (required for Docker and systemd inside LXCs):
```bash
for i in 101 102 103 104 105; do pct set $i --features nesting=1; done
```

Start everything:
```bash
for i in 101 102 103 104 105; do pct start $i; done
```

## Base Setup (all LXCs)

Run this inside each container after first boot:
```bash
apt update && apt upgrade -y
apt install -y curl git neovim sudo
```

## Bind Mounts

Bind mounts expose host ZFS datasets into containers. Set these after containers are created but before starting services.

```bash
# lxc-infra — no data mounts needed currently
# (files dataset is host-only cold storage)

# lxc-productivity
pct set 102 --mp0 /mnt/data/documents,mp=/mnt/documents

# lxc-photos
pct set 103 --mp0 /mnt/data/photos,mp=/mnt/photos

# lxc-media
pct set 104 --mp0 /mnt/data/music,mp=/mnt/music
pct set 104 --mp1 /mnt/data/media,mp=/mnt/media
pct set 104 --mp2 /mnt/data/downloads,mp=/mnt/downloads
```

> Bind mounts from host to unprivileged containers have UID/GID mapping issues. The host's root (UID 0) maps to UID 100000 inside the container. If services can't write to mounted paths, fix with:
```bash
# On the host, set ownership to the mapped UID
chown -R 100000:100000 /mnt/data/photos
```

## iGPU Passthrough (lxc-photos, lxc-media)

For Immich ML acceleration and Jellyfin QuickSync transcoding.

Add to `/etc/pve/lxc/103.conf` and `/etc/pve/lxc/104.conf`:
```
lxc.cgroup2.devices.allow: c 226:* rwm
lxc.mount.entry: /dev/dri dev/dri none bind,optional,create=dir
```

For lxc-media specifically (QuickSync needs card0 and renderD128 explicitly):
```
lxc.cgroup2.devices.allow: c 226:0 rwm
lxc.cgroup2.devices.allow: c 226:128 rwm
lxc.mount.entry: /dev/dri/card0 dev/dri/card0 none bind,optional,create=file
lxc.mount.entry: /dev/dri/renderD128 dev/dri/renderD128 none bind,optional,create=file
```

Check inside the container:
```bash
ls /dev/dri
# Should show card0 and renderD128
```

## Networking

Everything sits on `10.0.0.0/24` via the `vmbr0` bridge Proxmox creates on install. Static IPs are assigned at container creation via the `--net0` flag (see above) — no DHCP involved for servers.

```
10.0.0.1   — gateway/router
10.0.0.10  — theseus
10.0.0.20  — hyperion
10.0.0.101 — lxc-infra
10.0.0.102 — lxc-productivity
10.0.0.103 — lxc-photos
10.0.0.104 — lxc-media
10.0.0.105 — lxc-misc
```

Cloudflare Tunnel:
*Most* external traffic goes through a Cloudflare Tunnel running in lxc-infra (cloudflared). Services get subdomains at [my.domain](my.domain).

Tailscale:
Tailscale is installed on theseus with subnet routing. Mesh VPN for admin access via Proxmox VE, and for services that shouldn't be public like arr stack.

> Note: Run Tailscale with `--accept-dns=false` on all nodes to avoid MagicDNS conflicts with the local `10.0.0.0/24` subnet:
```bash
tailscale up --accept-dns=false
```

## LXC Tun Device (lxc-media, for Gluetun)

Gluetun needs `/dev/net/tun` for VPN tunnel creation. Add to `/etc/pve/lxc/105.conf`:
```
lxc.cgroup2.devices.allow: c 10:200 rwm
lxc.mount.entry: /dev/net/tun dev/net/tun none bind,create=file
```
```bash
# Inside lxc-media, check what IP qBittorrent traffic exits from
docker exec gluetun wget -qO- https://ipinfo.io
# Must show a ProtonVPN IP

# ProtonVPN setup in Gluetun .env:
VPN_SERVICE_PROVIDER=protonvpn
VPN_TYPE=wireguard
WIREGUARD_PRIVATE_KEY=<from ProtonVPN dashboard → Downloads → WireGuard config>
SERVER_COUNTRIES=<Country>  # or any country
```

## Git Workflow

LXCs only pull config/compose files from the homelab repo to get updates, which is why there are so so so many commits on this repo.

```bash
# On each LXC, clone the repo
git clone https://github.com/joshuaspiral/homelab /opt/homelab

# Deploy script on theseus runs git pull on each LXC
# scripts/homelab-deploy
for id in 101 102 103 104 105; do
  pct exec $id -- git -C /opt/homelab pull
done
```

---

# hyperion

Fedora Workstation install. Only turned on when needed (OCR pipeline, LLM inference, or as a desktop).

## Docker Setup

```bash
sudo dnf install -y docker docker-compose-plugin
sudo systemctl enable --now docker
sudo usermod -aG docker joshua
```

## Services (~/docker-compose.yaml)

llama-cpp runs Chandra-OCR for Paperless-ngx document OCR. Open-WebUI provides a chat interface backed by llama-cpp's OpenAI-compatible API.

```bash
cd ~
docker compose up -d
```

llama-cpp is on port 8080, Open-WebUI on port 3000. Both are LAN/Tailscale only.

## Wake-on-LAN

hyperion is off by default. The Paperless OCR pipeline wakes it via WOL before inference, then shuts it down after.

Ensure WOL is enabled in hyperion's BIOS/UEFI:
```bash
# On theseus or any LAN node
wakeonlan b4:2e:99:a0:7f:e9
```

Check that WOL is enabled on hyperion's NIC:
```bash
ethtool enp6s0 | grep Wake
# Should show: Wake-on: g
```
