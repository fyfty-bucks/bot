# Crypto Operations (Agent Runtime)

## Principle

Crypto is a survival skill. Use stable libraries, don't reinvent.
**Modular: one entity at a time, each plugs into the system like a puzzle piece.**
Scope: ETH and USD stablecoins. No exchange trading on start.

---

## Stack (stable libraries only)

| Library | Purpose | Maturity |
|---------|---------|----------|
| `web3.py` | On-chain: balance, transfer, contract calls | 7+ years, v7.13 |
| `openrouter` SDK | OpenRouter credit purchase via crypto | Official Python SDK |
| `eth-account` | Wallet management, key signing | Part of web3.py ecosystem |

**NEVER** write custom crypto primitives. Use libraries above.
Exchange library (ccxt or similar) deferred — not needed until trading phase.

---

## Modular Architecture

Each crypto capability = one module in `src/crypto/`:

```
src/crypto/
├── __init__.py          # Registry: available modules
├── wallet.py            # Entity 1: wallet read (balance, address)
├── budget.py            # Entity 2: spend tracking + alerts
├── topup.py             # Entity 3: OpenRouter credit purchase
└── earn.py              # Future: revenue strategies
```

### Build Order (one at a time, to be planned)

Build order and entity specs to be finalized during planning.
Each entity follows spike → test → implement pipeline.

---

## Top-Up Flow

```
budget low? → wallet has funds? → credits below threshold?
  → amount ≤$1: execute (L1, notify)
  → amount >$1: propose to user (L2, wait)
  → verify credits received
```

---

## Security

- Private keys in `secrets/wallet.env` — NEVER in code/git/logs/DB
- All send operations go through single function with escalation check
- Transaction signing happens in memory, key zeroed after
- Failed tx: log error, don't retry automatically (L2 for retry)
