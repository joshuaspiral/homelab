Create containers:
#todo continue the rest of the containers with proper allocations
```
pct create 103 local:vztmpl/debian-XX-standard_XX.XX-X_amd64.tar.zst \
  --hostname lxc-storage \
  --cores 1 \
  --memory 512 \
  --swap 512 \
  --rootfs local-lvm:20 \
  --net0 name=eth0,bridge=vmbr0,gw=10.0.0.1,ip=10.0.0.203/24 \
  --unprivileged 1 \
  --start 1
```
