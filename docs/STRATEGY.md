# Demo Strategy Notes

Educational overview of the starter rule wired in `executor.py`. This is **not** a proven edge.

## Market

Polymarket recurring BTC 15-minute Up/Down markets:

```text
btc-updown-15m-{unix_bucket}
```

Buckets are `floor(unix_time / 900) * 900`. Outcome tokens map to **Up** and **Down**.

## Strike (starter convention)

On each new bucket the bot records the **first TWAP sample** seen in that round as `strike`. Real settlement rules on Polymarket may differ; treat this as a **demo abstraction** for learning signal plumbing.

## Entry window

Only evaluate entries when seconds-to-expiry `tau` satisfies:

```text
ENTRY_WINDOW_END_SEC <= tau <= ENTRY_WINDOW_START_SEC
```

Defaults: `15 <= tau <= 90` (last 90 seconds of the round, but not the final 15).

## Side selection

For each side in `{Up, Down}`:

1. Read best ask.
2. Require ask in `[MIN_BUY_PRICE, MAX_BUY_PRICE]` (default 0.70–0.90).
3. Compute `lead = lead_vs_strike(twap, strike, side)`.
4. Require `lead > 0` (TWAP agrees with that side).
5. Size shares from `TRADE_SIZE_USD` with `POLYMARKET_MIN_SHARES` guard.

If multiple sides qualify, prefer the larger lead.

## Risk

- At most `MAX_TRADES_PER_ROUND` fills per bucket (default 1).
- Daily loss breaker: halt when cumulative PnL <= `-MAX_DAILY_LOSS_USD`.
- Paper mode does not invent settlement PnL; you can extend journaling after expiry.

## What this is not

- Not a backtested system
- Not advice to buy Up or Down near expiry
- Not a guarantee that TWAP lead predicts settlement

Use the structure to learn market discovery, feeds, risk, and paper execution — then replace the rule with your own research.
