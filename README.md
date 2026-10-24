# AIE Evidence Lab

Read-only x402 newcomer demand observatory. Python 3.12+, SQLite, standard library only.

```sh
PYTHONPATH=src python -m aie sources
PYTHONPATH=src python -m aie collect --source bazaar
PYTHONPATH=src python -m aie analyze --window-days 14
PYTHONPATH=src python -m aie report
PYTHONPATH=src python -m aie verify
```

Network collection is bounded to one GET with a timeout and identifiable User-Agent. No payment headers, wallet operations, paid calls, or automated 402 retries exist. `--fixture path.json` enables offline collector runs. The database is local and should be backed up/exported by the operator.

## Evidence interpretation

Listings are not companies, wallet addresses are not independent customers, and transfers are not API revenue. The current settlement collector is intentionally unimplemented because no public settlement interface with reliable request attribution was verified. Reports must retain this uncertainty. All synthetic fixtures are labeled as synthetic.
