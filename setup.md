Documentation for myself on setup!

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
# Get latest available template name
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

pct create 104 local:vztmpl/debian-12-standard_12.12-1_amd64.tar.zst \
  --hostname lxc-photos --cores 2 --memory 6144 --swap 512 \
  --rootfs local-zfs:30 \
  --net0 name=eth0,bridge=vmbr0,gw=10.0.0.1,ip=10.0.0.104/24 \
  --unprivileged 1

pct create 105 local:vztmpl/debian-12-standard_12.12-1_amd64.tar.zst \
  --hostname lxc-media --cores 3 --memory 3072 --swap 512 \
  --rootfs local-zfs:30 \
  --net0 name=eth0,bridge=vmbr0,gw=10.0.0.1,ip=10.0.0.105/24 \
  --unprivileged 1

pct create 106 local:vztmpl/debian-12-standard_12.12-1_amd64.tar.zst \
  --hostname lxc-misc --cores 1 --memory 512 --swap 512 \
  --rootfs local-zfs:10 \
  --net0 name=eth0,bridge=vmbr0,gw=10.0.0.1,ip=10.0.0.106/24 \
  --unprivileged 1
```

Enable nesting (required for Docker and systemd inside LXCs):
```bash
for i in 101 102 104 105 106; do pct set $i --features nesting=1; done
```

Start everything:
```bash
for i in 101 102 104 105 106; do pct start $i; done
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
# lxc-infra: no data mounts needed
# (files dataset is host-only cold storage)

# lxc-productivity
pct set 102 --mp0 /mnt/data/documents,mp=/mnt/documents

# lxc-photos
pct set 104 --mp0 /mnt/data/photos,mp=/mnt/photos

# lxc-media
pct set 105 --mp0 /mnt/data/music,mp=/mnt/music
pct set 105 --mp1 /mnt/data/media,mp=/mnt/media
pct set 105 --mp2 /mnt/data/downloads,mp=/mnt/downloads
```

> Bind mounts from host to unprivileged containers have UID/GID mapping issues. The host's root (UID 0) maps to UID 100000 inside the container. If services can't write to mounted paths, fix with:
```bash
# On the host, set ownership to the mapped UID
chown -R 100000:100000 /mnt/data/photos
```

## iGPU Passthrough (lxc-photos, lxc-media)

For Immich ML acceleration and Jellyfin QuickSync transcoding.

Add to `/etc/pve/lxc/104.conf` and `/etc/pve/lxc/105.conf`:
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

Everything sits on `10.0.0.0/24` via the `vmbr0` bridge Proxmox creates on install. Static IPs are assigned at container creation via the `--net0` flag.

```
10.0.0.1   - gateway/router
10.0.0.10  - theseus
10.0.0.20  - hyperion
10.0.0.101 - lxc-infra
10.0.0.102 - lxc-productivity
10.0.0.104 - lxc-photos
10.0.0.105 - lxc-media
10.0.0.106 - lxc-misc
```

Cloudflare Tunnel: external traffic goes through cloudflared in lxc-infra. Services get subdomains at joshuaspiral.xyz. No open inbound ports on the router.

Tailscale: installed on theseus host with subnet routing enabled. Provides VPN access to the whole 10.0.0.0/24 network. For Proxmox VE, arr stack. 

> Run Tailscale with `--accept-dns=false` on all nodes. To fix local DNS resolution on the 10.0.0.0/24 subnet, because Tailscale's MagicDNS rewrites `/etc/resolv.conf` and breaks local DNS resolution.
```bash
tailscale up --accept-dns=false
```

## LXC Tun Device (lxc-media, for Gluetun)

Gluetun needs `/dev/net/tun` for VPN tunnel creation. Add to `/etc/pve/lxc/105.conf`:
```
lxc.cgroup2.devices.allow: c 10:200 rwm
lxc.mount.entry: /dev/net/tun dev/net/tun none bind,create=file
```

ProtonVPN WireGuard key: get from ProtonVPN dashboard → Downloads → WireGuard configuration. Add to lxc-media `.env` as `PROTONVPN_PRIVATE_KEY`.

Verify no IP leak after starting Gluetun:
```bash
docker exec gluetun wget -qO- https://ipinfo.io
```

## Git Workflow

LXCs only pull from the homelab repo: they never commit.

```bash
# On each LXC, clone the repo once
git clone https://github.com/joshuaspiral/homelab /opt/homelab
```

Deploy script (`scripts/homelab-deploy`) runs git pull on each LXC from theseus:
```bash
for ct in 101 102 104 105 106; do
  pct exec $ct -- bash -c "cd /opt/homelab && git pull"
done
```

Note: After a compose change, manually run `docker compose up -d` in the affected container.

---

# hyperion

OS: Fedora Workstation. Only on when needed for OCR, LLM inference, or desktop use.

## Docker Setup

```bash
sudo dnf install -y docker docker-compose-plugin
sudo systemctl enable --now docker
sudo usermod -aG docker joshua
```

## Services (~/compose.yaml)

llama-cpp serves Chandra-OCR on port 8080. Open-WebUI is on port 3000:

```bash
cd ~
docker compose up -d
```

## Wake-on-LAN

hyperion is off by default. The Paperless OCR pipeline wakes it before inference via a magic packet, then SSHes in to shut it down after.

Ensure WOL is enabled in BIOS/UEFI, then verify:
```bash
ethtool enp6s0 | grep Wake
# Should show: Wake-on: g
```

Manual wake from theseus or any LAN node:
```bash
wakeonlan b4:2e:99:a0:7f:e9
```
