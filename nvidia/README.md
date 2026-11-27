# NVIDIA host setup

Done once per machine, whichever card it has. The lab runs Rocky Linux; the steps are the same on
any distribution with packages for the three pieces below.

## 1. Driver

All three cards here are Blackwell (GB20x), CUDA compute capability **12.0** (`sm_120`): the
GeForce RTX 5080 and 5090 and the RTX PRO 6000 Blackwell workstation card alike. They need:

- the **open** NVIDIA kernel modules (Blackwell has no proprietary-module support), driver 570 or
  later
- a CUDA 12.8 or later userspace inside the container, which the pinned llama.cpp image has

Check it:

```bash
nvidia-smi --query-gpu=name,memory.total,driver_version,compute_cap --format=csv
```

## 2. NVIDIA Container Toolkit

Lets Docker hand the GPU to a container.

```bash
# RHEL / Rocky / Fedora
curl -fsSL https://nvidia.github.io/libnvidia-container/stable/rpm/nvidia-container-toolkit.repo \
  | sudo tee /etc/yum.repos.d/nvidia-container-toolkit.repo
sudo dnf install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# check: the container sees the card
docker run --rm --gpus all ubuntu nvidia-smi
```

Debian and Ubuntu: NVIDIA's install guide has the `apt` equivalent.

## 3. Docker Engine with the Compose plugin

`docker compose version` should print v2. Docker's own repository is the reliable source on RHEL
derivatives (`docker-ce`, `docker-compose-plugin`).

## 4. Models

The stacks read GGUF files from a directory you choose (`MODEL_DIR` in `.env`), mounted read-only.
The Hugging Face CLI downloads them:

```bash
pip install -U "huggingface_hub[cli]"
hf download <repo> <file or --include pattern> --local-dir <MODEL_DIR>/<name>
```

Each variant's `.env.example` names the exact repository and file we used.

## Power

A workstation card at full power can draw 600 W on its own. On a UPS sized for less, cap it; every
RTX PRO 6000 number in [`../docs/measured.md`](../docs/measured.md) except one was taken at 400 W,
and the cap cost little:

```bash
sudo nvidia-smi -pl 400      # resets at reboot; a systemd oneshot makes it stick
```
