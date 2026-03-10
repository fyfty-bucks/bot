# Phase 4: Deploy to RPi

**Status:** NOT STARTED

---

## Scope

Production deployment on Raspberry Pi 4. Continuous operation, monitoring, branch model.
Includes Anthropic direct access for prompt caching.

## Dependencies

Phase 3 (Telegram Bot) — bot must work before deploying

## Deliverables

- [ ] Git hooks + deploy script
- [ ] Systemd unit + watchdog
- [ ] Cron: health check, reports, weekly research
- [ ] Swap file, secrets on device
- [ ] SSH from Cursor for live ops
- [ ] Branch model: `main` (stable, RPi deploy) / `dev` (developer + model)
- [ ] Anthropic API proxy for prompt caching (see below)

## Anthropic direct access (spike findings from Phase 2)

Anthropic blocks Russian IPs. Prompt caching via OpenRouter is broken (known bugs).
Direct access enables native prompt caching: **90% input cost reduction**.

Haiku 4.5 prompt cache pricing:
- Write: $1.25/M tokens (1.25x normal)
- Read: $0.10/M tokens (0.1x normal)
- Breakeven: 1.67 cache hits per write
- TTL: 5 min (ephemeral) or 1h with `ttl` field

**Options (ranked):**

| # | Method | Cost | Control | Prompt cache |
|---|---|---|---|---|
| 1 | **VPS proxy** (Hetzner/OVH) | $3-5/mo | Full | Yes |
| 2 | Cloudflare Workers (JS) | Free 100K req/day | Medium | Yes |
| 3 | AITUNNEL.ru (RU proxy) | ~2x Anthropic price | Low | Unknown |

**Decision:** VPS proxy (option 1). nginx reverse proxy or SSH tunnel from RPi.
Full control, lowest cost, prompt caching works natively.
CF Workers as backup. AITUNNEL as emergency.

Implementation: `src/llm/client.py` already abstracts base_url — switch
from OpenRouter to direct Anthropic endpoint per model.

## Risks

- ARM64 dependency compatibility (wheels)
- SD card wear from SQLite writes (WAL mitigates)
- Network reliability for API calls
- Power/heat on sustained operation
- VPS adds $3-5/mo fixed cost (offset by 90% cache savings)

## Gate

Agent running on RPi 24/7. Cron jobs active. Watchdog monitoring.
SSH access from Cursor confirmed. Anthropic proxy operational.
