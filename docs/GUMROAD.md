# Gumroad Listing Copy

Suggested packaging text for selling this starter kit. Edit freely.

---

## Title

Polymarket BTC 15-Minute Trading Bot Starter Kit (Python, Paper-Trade First)

## Subtitle

Educational dry-run bot scaffold for Polymarket `btc-updown-15m` markets — market discovery, TWAP helpers, risk limits, paper journal. No profit promises.

## Price suggestion

**$59**

(Optional: discount launch price $39, then $59.)

---

## Bullet highlights

- **Paper-trade first**: `DRY_RUN=true` by default; never signs orders in dry-run
- **BTC 15m Up/Down focus**: slug math for `btc-updown-15m-{unix_bucket}`
- **Market discovery**: Gamma slug fetch + token map parsing with cache
- **Feed stubs**: RTDS/Chainlink TWAP + Binance ticker structure with synthetic demo fallback so `main.py` starts offline
- **Demo entry rule**: late-window + TWAP lead + ask price band + risk checks
- **Risk manager**: daily loss breaker, per-round trade cap, min-share sizing
- **JSONL journal**: inspect paper fills under `data/journal.jsonl`
- **Tests included**: pytest suite runs fully offline
- **Docker + .env.example**: clean buyer onboarding
- **Clear disclaimers**: educational only; risk of loss; not financial advice

---

## Who this is for

- Developers who want a **readable Python scaffold** to learn Polymarket CLOB/Gamma plumbing
- Quants / hobbyists exploring **15-minute BTC Up/Down** market structure
- Buyers who prefer **dry-run / paper** before touching live keys
- People building their **own** strategies who need discovery, feeds, risk, and journaling wired together

## Who this is not for

- Anyone expecting a “set and forget” money printer
- Non-technical users who will not read code or run pytest
- Anyone seeking financial advice or guaranteed returns

---

## What’s included

- Full Python project source (starter modules listed in README)
- `README.md`, `docs/STRATEGY.md`, this listing doc
- `requirements.txt`, Dockerfile, LICENSE (personal use)
- Offline unit tests

## What you need

- Python 3.11+
- Comfortable with terminal, venv, and reading Python
- Optional: Polymarket account / keys **only if** you later disable dry-run (advanced, at your own risk)

---

## FAQ

**Q: Does this make money out of the box?**  
A: No. It is an educational starter. The demo rule is for learning signal flow, not a claimed edge.

**Q: Will it place live trades?**  
A: Not while `DRY_RUN=true` (default). Live mode requires keys and your explicit config change. You accept full responsibility.

**Q: Do I need API secrets to try it?**  
A: No. Dry-run + synthetic feeds work without secrets.

**Q: Is this affiliated with Polymarket?**  
A: No. Independent educational software.

**Q: Can I resell this kit?**  
A: No. License is personal use for the Gumroad purchaser. See LICENSE.

**Q: Refunds?**  
A: Set your Gumroad refund policy clearly (e.g. 7-day if files unused / unsatisfied with documentation quality — not for trading losses).

---

## Disclaimer (paste into Gumroad description)

This product is for **education and research only**. It is **not financial, investment, tax, or trading advice**. Cryptocurrency and prediction-market trading involve **substantial risk of loss**. You can lose some or all of your capital. Simulated results and demo strategies **do not guarantee** future performance. The seller makes **no profit promises** and accepts no liability for trading outcomes. Use dry-run mode. Audit all code before any live use. By purchasing you acknowledge these risks.

---

## Suggested Gumroad short description

Build and study a paper-trade-first Python bot for Polymarket BTC 15-minute Up/Down markets. Includes discovery, feed stubs, risk controls, journaling, tests, and Docker. Dry-run by default. Educational — not financial advice.
