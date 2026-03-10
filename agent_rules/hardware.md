# Hardware: Raspberry Pi 4 Model B

## Specs

- SoC: BCM2711, quad-core Cortex-A72 (ARM v8) @ 1.8GHz
- RAM: 8GB LPDDR4
- Storage: microSD (watch write cycles) or USB SSD
- OS: Raspberry Pi OS / Ubuntu Server (ARM64)
- Package manager: apt

---

## Health Checks

```bash
vcgencmd measure_temp        # CPU temperature
vcgencmd get_throttled       # Throttling state
free -m                      # Memory
df -h                        # Disk
uptime                       # Load average
```

---

## Constraints

| Don't | Why |
|-------|-----|
| Heavy ML models locally | 8GB RAM, no GPU |
| Large Docker images | SD card space |
| Frequent disk writes | SD card wear |
| Compile large C++ deps | Slow ARM, may OOM |

---

## Preferred Stack

| Component | Choice | Reason |
|-----------|--------|--------|
| Python | 3.11+ | Pre-installed, ecosystem |
| ORM | Peewee | Lightweight, mature |
| Vector DB | TBD (spike: ARM64 compat test) | Embedded, must verify on RPi |
| HTTP | httpx / aiohttp | Async, low overhead |
| Task queue | asyncio | No Redis/Celery overhead |
| Process mgmt | systemd | Native, reliable |

---

## Systemd Unit Template

```ini
[Unit]
Description=Agent Service
After=network-online.target

[Service]
ExecStart=/usr/bin/python3 /home/agent/src/main.py
Restart=on-failure
RestartSec=10
WorkingDirectory=/home/agent
EnvironmentFile=/home/agent/secrets/agent.env

[Install]
WantedBy=multi-user.target
```

---

## Network

- Stable internet required for API calls
- Retry with exponential backoff
- Cache API responses where possible
- Monitor bandwidth (mobile hotspot scenario)
