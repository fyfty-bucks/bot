# Phase 5: Survival I — CustDev + First Revenue

**Status:** NOT STARTED

---

## Scope

Marketing-oriented phase. User research, feature discovery, first monetization.
Goal: find what users will pay for and deliver it.

## Dependencies

Phase 4 (Deploy) — agent running on RPi with Telegram bot

## Deliverables

**Research:**
- [ ] CustDev plan: KANO model for feature discovery
- [ ] User interviews / surveys via Telegram
- [ ] Competitive analysis: what similar bots charge for
- [ ] Feature prioritization: impact vs effort matrix

**Monetization:**
- [ ] First paid feature (based on CustDev insights)
- [ ] Activate payment flow (Stars / TON)
- [ ] Pricing experiments

**Operations:**
- [ ] Budget optimization (minimize token spend per response)
- [ ] Owner alerts via Telegram on critical events
- [ ] Cost/revenue dashboard in `info` command

**Agent capabilities (post-KANO, if demanded):**
- [ ] MCP client — connect external tool servers via Model Context Protocol
  - MCP Python SDK v1.26, JSON-RPC 2.0, stdio/SSE transport
  - ToolRegistry wraps MCP tools as `Tool` instances (same contract)
- [ ] Web crawler tool — `web_search(query) -> markdown`
  - Options: Crawl4AI (61k stars, async, needs sync wrapper), Supacrawl (lightweight CLI)
  - Registered as a tool in ToolRegistry, used by agent loop
- [ ] Additional MCP servers as plugins (filesystem, database, APIs)

## Success Criteria

- First paying user
- Revenue > $0
- Clear understanding of what users value

## Gate

At least one paid feature live. Payment flow working. User feedback loop established.
