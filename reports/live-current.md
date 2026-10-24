# x402 Newcomer Demand Observatory

Generated at 2026-10-24T17:44:46Z (UTC). Source: Coinbase Bazaar discovery API.

## Coverage

Snapshot `3b02b9c6-4463-44b3-84c7-76c094833196` collected 10 pages and 1,000 unique resource observations. The API advertised 40,036 records. Status: **PARTIAL_SNAPSHOT**. The reported 1000 is a bounded sample, not complete catalog coverage. The live response pagination metadata changed from 39,774 in an earlier request to 40,036 in this collection, so catalog size is time-varying.

## Payment evidence

No public settlement collector was configured and no ledger transfers were independently verified in this run. Marketplace quality telemetry is not a payment receipt. No resource-level purchase attribution is available.

## Analysis and decision

There is one discovery snapshot, no longitudinal follow-up, and no verified payment records. New listing does not mean new company; payer addresses, if later observed, will not establish customer independence. Decision: **INSUFFICIENT_DATA**. Realized LeftSock income: **$0**.

## Reproduction

```sh
PYTHONPATH=src python -m aie collect --source bazaar --max-pages 10 --db data/evidence.sqlite
PYTHONPATH=src python -m aie analyze --window-days 14 --db data/evidence.sqlite
PYTHONPATH=src python -m aie report --db data/evidence.sqlite
PYTHONPATH=src python -m aie verify --db data/evidence.sqlite
PYTHONPATH=src python -m unittest discover -s tests -v
```
