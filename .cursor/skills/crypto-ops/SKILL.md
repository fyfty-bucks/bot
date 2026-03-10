# Skill: Implement Crypto Modules

Guide for Opus 4.6 when coding agent's crypto capabilities.

---

## When to Use

- Building any module in `src/crypto/`
- Integrating web3.py, openrouter SDK, or eth-account
- Adding budget tracking or payment flow

---

## Reference

Agent specs: `agent_rules/crypto.md`, `agent_rules/crypto-earn.md`

---

## Libraries (use these, don't reinvent)

| Library | Purpose |
|---------|---------|
| `web3.py` | On-chain: balance, transfer, contracts |
| `openrouter` | OpenRouter Python SDK (credit purchase) |
| `eth-account` | Wallet management (part of web3.py) |

Scope: ETH and USD stablecoins. No exchange trading on start.
Exchange library deferred to future phases.

Install: `pip install web3 openrouter`

---

## Build Order

Build order to be finalized during planning.
Each module: own test file in `tests/crypto/`, follows spike → test → implement.

---

## Testing

- Mock ALL blockchain/API calls (never real wallet in tests)
- Test budget alerts at boundaries (79%, 80%, 95%, 96%)
- Test escalation logic (L1 vs L2 threshold)
- Test transaction failure paths
