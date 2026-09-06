# Polymarket BTC 15-Minute Up/Down — Starter Kit

Educational, **paper-trade-first** starter for Polymarket BTC 15-minute Up/Down markets (`btc-updown-15m-{unix_bucket}`).

**Dry-run by default. No profit promises. No secrets bundled.**

---

## Disclaimer

This product is for **education and research only**. It is **not financial, investment, or trading advice**. Prediction markets and crypto involve **risk of loss**, including loss of capital. Simulated or past results **do not guarantee** future results. You are solely responsible for how you use this code. The authors make **no warranties** and **no profit guarantees**.

---

## What you get

| Module | Role |
|--------|------|
| `config.py` | Env-based settings; validates keys only when live |
| `market_discovery.py` | Bucket/slug math + Gamma event fetch/cache |
| `data_feeds.py` | Price/TWAP feed abstractions + demo synthetic WS fallback |
| `twap_math.py` | Lead vs strike, z-score, band, expiry helpers |
| `clob_client.py` | CLOB wrapper; never signs in `DRY_RUN` |
| `risk_manager.py` | Daily loss breaker, round limits, min shares |
| `executor.py` | Demo entry rule + paper journal fills |
| `journal.py` | JSONL append journal under `data/` |
| `main.py` | Async loop with clear dry-run banner |

---

## Requirements

- Python 3.11+ (3.12 recommended)
- Linux / macOS / WSL (Windows OK with care)

---

## Install

```bash
cd polymarket-bot-starter
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Keep `DRY_RUN=true` in `.env` until you understand every path.

---

## Run tests (offline)

```bash
source .venv/bin/activate
python -m pytest -q
```

All unit tests are network-free.

---

## Dry-run (default)

```bash
source .venv/bin/activate
python main.py
```

You should see a banner confirming `DRY_RUN=True`, educational disclaimer text, and a 1-second evaluation loop. Feeds start in **synthetic demo mode** so the process runs even if WebSockets fail. Paper fills (if any) append to `data/journal.jsonl`.

Stop with `Ctrl+C` (graceful shutdown).

---

## Docker

```bash
docker build -t polymarket-bot-starter .
docker run --rm -it --env-file .env polymarket-bot-starter
```

Default CMD is `python main.py` with `DRY_RUN=true`.

---

## Configuration highlights

See `.env.example` for the full list. Important defaults:

- `DRY_RUN=true`
- Entry window: last `90`–`15` seconds of the 15m round
- Buy band: ask between `0.70` and `0.90`
- `TRADE_SIZE_USD=5`, `MAX_DAILY_LOSS_USD=25`, `MAX_TRADES_PER_ROUND=1`
- `POLYMARKET_MIN_SHARES=5`

When `DRY_RUN=false`, `config.validate()` requires `POLYMARKET_PRIVATE_KEY` and `POLYMARKET_FUNDER_ADDRESS`. Live trading is advanced, optional, and **not recommended** until you have audited the code yourself.

---

## Architecture (short)

1. **Discover** the current `btc-updown-15m-{bucket}` market via Gamma (or a local demo stub).
2. **Feeds** update spot (Binance-shaped) and TWAP (RTDS/Chainlink-shaped); demo mode synthesizes prices.
3. **Strike** is set from the first TWAP sample of the round (demo-friendly).
4. **DemoExecutor** checks time-to-expiry, TWAP lead side, ask band, and risk limits.
5. **ClobWrapper** returns simulated fills in dry-run; journaling records paper activity.

This is a **starter**, not a production alpha engine. Extend strategy, feeds, and execution carefully.

---

## Docs

- [docs/STRATEGY.md](docs/STRATEGY.md) — demo rule explanation
- [docs/GUMROAD.md](docs/GUMROAD.md) — listing copy for sellers / packaging notes

---

## License

Proprietary personal-use license for Gumroad purchasers. See [LICENSE](LICENSE).

---

## Support mindset

Read the code. Run the tests. Stay in dry-run. Size small if you ever go live. Assume you can lose money.
