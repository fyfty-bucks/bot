# Shell Rules (Agent Runtime)

## Principle

Agent operates on RPi with root access via sudo.
**Minimal privilege: use sudo only when required.**

---

## Privilege Escalation

- Secrets (SSH key, sudo password) in `secrets/` — NEVER in code/git
- Prefer non-root operations where possible
- Log every sudo command executed

---

## Allowed Operations

| Operation | Command | sudo |
|-----------|---------|------|
| Package install | `apt install -y X` | Yes |
| Service manage | `systemctl start/stop/enable X` | Yes |
| System info | `df`, `free`, `uptime`, `vcgencmd` | No |
| Python packages | `pip install X` | No (venv) |
| File operations | `cp`, `mv`, `mkdir` in agent dirs | No |
| Network check | `ping`, `curl`, `ip addr` | No |
| Cron/systemd units | Write + `systemctl daemon-reload` | Yes |

---

## Forbidden Without User Confirmation (L2+)

- `rm -rf` on system directories
- `fdisk`, `mkfs` — disk partitioning
- `systemctl disable` critical services (ssh, networking)
- `rpi-update` — firmware updates
- Kernel parameter changes (`sysctl`, `/boot/config.txt`)
- Any command that could break SSH access

---

## Safety Checks Before System Commands

Before executing any shell command, agent checks against a blocklist
of dangerous patterns. If matched → escalate to user, don't execute.

Blocklist: `rm -rf /`, `mkfs`, `fdisk`, `rpi-update`, and any command
that could break SSH access. Implementation in `src/system/safety.py`.
