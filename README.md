# AIE Evidence Lab

Read-only x402 newcomer demand observatory. Python 3.12+, SQLite, and the small `eth-account` dependency for EIP-712 signature verification.

```sh
PYTHONPATH=src python -m aie sources
PYTHONPATH=src python -m aie collect --source bazaar
PYTHONPATH=src python -m aie analyze --window-days 14
PYTHONPATH=src python -m aie report
PYTHONPATH=src python -m aie verify
PYTHONPATH=src python -m aie verify-transfer --tx 0x… --event-index 51
PYTHONPATH=src python -m aie verify-purchase --evidence proof.json
```

Network discovery is bounded, and the settlement collector uses read-only Base RPC. No payment headers, wallet operations, paid calls, or automated 402 retries exist. `--fixture path.json` enables offline discovery collection. The evidence database is local except for the separate GitHub evidence-data branch observations.

## Evidence interpretation

Listings are not companies, wallet addresses are not independent customers, and transfers are not API revenue. Base USDC transfer verification proves only ledger movement and merchant-address association. Resource attribution requires a valid x402 signed offer and receipt, authorized resource signing key evidence, and a matching finalized transfer. See [Phase VIII methodology](docs/phase-viii-attribution.md) and [reverified transfer evidence](reports/evidence/phase-viii-base-transfers.json). All synthetic fixtures are labeled as synthetic and are not marketplace evidence.
