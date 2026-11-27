# Security defaults, and why

A local model server is a program that accepts arbitrary text and spends your GPU on it. Treat it
like any other network service.

## What the stacks do by default

- **Listen on `127.0.0.1` only.** Compose publishes the port as `127.0.0.1:8080`. Nothing else on
  the network can reach it until you change `BIND` in `.env`.
- **Refuse to start without an API key.** `LLAMA_API_KEY` is required; llama-server then rejects
  any request without `Authorization: Bearer <key>`. The key is passed as an environment variable,
  so it does not appear in the process list or the container's command line.
- **Mount the models read-only.** The server cannot alter the weights it serves.
- **Pin the image by digest.** A tag such as `server-cuda` moves whenever upstream publishes; a
  digest does not. Upgrading is a deliberate edit you can test and roll back.

## Opening it to your LAN

Set `BIND` to the machine's LAN address (or `0.0.0.0`) and keep the key. Then restrict who can
reach the port in the host firewall, by source address:

```bash
# firewalld: allow one client machine, nothing else
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="192.168.1.50/32" port port="8080" protocol="tcp" accept'
sudo firewall-cmd --reload
```

Docker publishes ports through its own rules, which can bypass a host firewall's zone settings.
Check from another machine that only the clients you allowed can connect.

## Never forward it to the internet

Do not port-forward these servers. llama.cpp and mlx-lm are not hardened against hostile traffic,
and automated scanners find exposed model servers within hours. For remote use, put the machine on
a private overlay network (WireGuard, Tailscale) so the server never has a public address, or put
an authenticating front door in front of it (for example Cloudflare Tunnel with Access) so that
unauthenticated traffic never reaches it.

## Keep the key out of files you share

`.env` holds the key and is in `.gitignore`. Never commit it, paste it into an issue, or bake it
into an image. If it leaks, generate a new one and restart: `docker compose up -d` picks up the
change.
