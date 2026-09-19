# Customer Ledger Migration Plan

## Goal

Move `customer.balance_cents` from the legacy `customers` table into an append-only `ledger_entries` table without write downtime.

## Proposed rollout

1. Deploy the new `ledger_entries` table.
2. Start dual-writing new balance changes to both tables.
3. Backfill historical balances in batches of 10,000 customers.
4. Compare aggregate totals between the legacy column and the ledger.
5. Switch reads to `SUM(ledger_entries.amount_cents)`.
6. After 24 hours, remove the legacy write path.

## Current rollback

If the new read path is slow or inconsistent, switch reads back to `customers.balance_cents` and stop the backfill.

## Known constraints

- The legacy write path has no idempotency key.
- Backfill and live dual-writes can overlap for the same customer.
- One downstream report reads from a read replica with up to five minutes of lag.
- The proposed aggregate comparison has no per-customer mismatch report.

## Open question

What evidence is sufficient before the read cutover, and how can rollback avoid losing writes accepted only by the new path?
