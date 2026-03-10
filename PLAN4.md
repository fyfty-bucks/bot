# Phase 4: Deploy to RPi

**Status:** NOT STARTED

---

## Scope

Production deployment on Raspberry Pi 4. Continuous operation, monitoring, branch model.

## Dependencies

Phase 3 (Telegram Bot) — bot must work before deploying

## Deliverables

- [ ] Git hooks + deploy script
- [ ] Systemd unit + watchdog
- [ ] Cron: health check, reports, weekly research
- [ ] Swap file, secrets on device
- [ ] SSH from Cursor for live ops
- [ ] Branch model: `main` (stable, RPi deploy) / `dev` (developer + model)

## Risks

- ARM64 dependency compatibility (wheels)
- SD card wear from SQLite writes (WAL mitigates)
- Network reliability for API calls
- Power/heat on sustained operation

## Gate

Agent running on RPi 24/7. Cron jobs active. Watchdog monitoring.
SSH access from Cursor confirmed.
