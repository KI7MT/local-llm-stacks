# Rocky Linux 9 with an NVIDIA Blackwell card

How the lab's Blackwell machines were built on Rocky Linux 9, and what went wrong the first time.
Everything here was done on real hardware; the dates say when.

| Machine | Card | Built | Driver now | Notes |
|---|---|---|---|---|
| Threadripper workstation, bare metal | RTX PRO 6000 Blackwell 96 GB | 2026-02-01, driver 590.48.01 | 610.57.04 on Rocky 9.8, kernel 5.14.0-687.44.1.el9_8 | CUDA toolkit 13.1, Container Toolkit 1.20.0 |
| Proxmox VM, GPU passed through | RTX 5080 16 GB | 2026-06-08 | | Rocky 9 cloud image, q35 + OVMF |
| Ryzen 9950X3D desktop, bare metal | RTX 5090 32 GB | early 2026 | | NVIDIA's RHEL 9 repository, CUDA toolkit 12.8 |

The workstation and the VM were installed the same way: NVIDIA's CUDA repository for RHEL 9 and
the **open** kernel module built by DKMS. For the 5090 only the repository and toolkit steps were
kept, not the driver step.

## The one rule: open kernel modules

Blackwell (RTX 50 series, RTX PRO Blackwell) works **only** with NVIDIA's open kernel modules.
The proprietary module installs and even loads, then fails to bring the card up:

```
RmInitAdapter failed! (0x22:0x56:1050)
... requires use of the NVIDIA open kernel modules
```

That is the error to recognise. On Rocky 9 the fix is the `open-dkms` stream instead of
`latest-dkms`.

## Steps

Run as root, or with `sudo`.

**1. Update and reboot first.** The driver is built against the running kernel's headers; a kernel
update in the same session leaves you with a module built for the wrong kernel.

```bash
dnf -y update && reboot
```

**2. EPEL, on its own.** DKMS comes from EPEL, and it will not resolve in the same transaction
that installs `epel-release`.

```bash
dnf -y install epel-release
dnf -y install kernel-devel-$(uname -r) kernel-headers dkms
```

**3. NVIDIA's CUDA repository for RHEL 9.** Add the network repository file. Do not install a
version-numbered `cuda-repo-*.rpm`: those disappear when NVIDIA moves to the next version.

```bash
dnf config-manager --add-repo \
  https://developer.download.nvidia.com/compute/cuda/repos/rhel9/x86_64/cuda-rhel9.repo
```

**4. The driver, open modules.**

```bash
dnf -y module install nvidia-driver:open-dkms
reboot
```

**5. Check.**

```bash
nvidia-smi --query-gpu=name,driver_version,compute_cap --format=csv
cat /proc/driver/nvidia/version          # should say "Open Kernel Module"
```

If `nvidia-smi` cannot talk to the driver after the reboot, the module was not built for the
running kernel. Build it and load it:

```bash
dkms status                               # "added" instead of "installed" means not built
dkms autoinstall -k $(uname -r)
modprobe nvidia
```

**6. CUDA toolkit: only if you compile CUDA code.** The container stacks in this repository do not
need it; the CUDA libraries are in the image. To build for Blackwell (`sm_120`) you need CUDA 12.8
or later:

```bash
dnf -y install cuda-toolkit-13-1          # the lab's version; cuda-toolkit-12-8 is the minimum
```

**7. Docker and the NVIDIA Container Toolkit:** [`../README.md`](../README.md).

## Things that cost time

- **Minimal cloud images have no `lspci`.** To check that a passed-through card is visible before
  installing anything, read sysfs instead: `grep -l 0x10de /sys/bus/pci/devices/*/vendor` (NVIDIA's
  vendor ID).
- **A kernel update during the install.** A fresh cloud image ships an older kernel than the
  repositories, so `dnf` pulls a new one mid-install and the module gets built for the old one.
  Step 1 avoids it; the `dkms autoinstall` in step 5 repairs it.
- **`libnvidia-egl-gbm` version mismatch after a driver update.** Seen on the workstation; it only
  affects EGL and desktop graphics, not CUDA or the containers. Reboot after every driver update
  first. The lab's workaround at the time was a symlink from the old library name to the new
  one, which is a stopgap, not a fix.
- **The first install on the workstation was removed and done again** (2026-02-01, the same
  command both times). If an install goes wrong, `dnf remove '*nvidia*'` and start again from
  step 4 rather than patching it up.

## Not covered

- **Secure Boot.** The lab's machines run with it off. With it on, the DKMS-built module has to be
  signed with a key enrolled through `mokutil`; that has not been tested here.
- **Rocky Linux 10.** When these were built, NVIDIA's repository supported RHEL 9 only.
