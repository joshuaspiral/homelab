# LXC Provisioning

To provision the complete 100-level container architecture on the `local-zfs` pool:

```bash
# 1. Update templates and download Debian 12
pveam update
pveam download local debian-12-standard_12.12-1_amd64.tar.zst

# 2. Provision Containers
pct create 101 local:vztmpl/debian-12-standard_12.12-1_amd64.tar.zst --hostname lxc-infra --cores 1 --memory 1536 --swap 512 --rootfs local-zfs:20 --net0 name=eth0,bridge=vmbr0,gw=10.0.0.1,ip=10.0.0.101/24 --unprivileged 1
pct create 102 local:vztmpl/debian-12-standard_12.12-1_amd64.tar.zst --hostname lxc-productivity --cores 2 --memory 2560 --swap 512 --rootfs local-zfs:40 --net0 name=eth0,bridge=vmbr0,gw=10.0.0.1,ip=10.0.0.102/24 --unprivileged 1
pct create 103 local:vztmpl/debian-12-standard_12.12-1_amd64.tar.zst --hostname lxc-storage --cores 1 --memory 512 --swap 512 --rootfs local-zfs:20 --net0 name=eth0,bridge=vmbr0,gw=10.0.0.1,ip=10.0.0.103/24 --unprivileged 1
pct create 104 local:vztmpl/debian-12-standard_12.12-1_amd64.tar.zst --hostname lxc-photos --cores 2 --memory 3072 --swap 512 --rootfs local-zfs:30 --net0 name=eth0,bridge=vmbr0,gw=10.0.0.1,ip=10.0.0.104/24 --unprivileged 1
pct create 105 local:vztmpl/debian-12-standard_12.12-1_amd64.tar.zst --hostname lxc-media --cores 3 --memory 3072 --swap 512 --rootfs local-zfs:30 --net0 name=eth0,bridge=vmbr0,gw=10.0.0.1,ip=10.0.0.105/24 --unprivileged 1
pct create 106 local:vztmpl/debian-12-standard_12.12-1_amd64.tar.zst --hostname lxc-homeauto --cores 1 --memory 1024 --swap 512 --rootfs local-zfs:20 --net0 name=eth0,bridge=vmbr0,gw=10.0.0.1,ip=10.0.0.106/24 --unprivileged 1

# 3. Enable Nesting for systemd/Docker compatibility
for i in {101..106}; do pct set $i -features nesting=1; done

# 4. Start all containers
for i in {101..106}; do pct start $i; done
```
