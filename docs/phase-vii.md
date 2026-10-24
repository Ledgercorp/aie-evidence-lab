# Phase VII sources and decisions

Base JSON-RPC: https://base-rpc.publicnode.com. Read-only calls verified eth_chainId=0x2105, safe block retrieval, and eth_getLogs for canonical Base USDC transfer topic. The safe-block bounded collector stores transaction hash, event index, sender/recipient, base units, six decimals, block number/time and block hash. A payTo address match is MERCHANT_ASSOCIATED only; resource invocation and independent customer remain unknown. USD peg is not assumed.

The AIE collector is bounded to at most 500 safe blocks and 25 published payTo recipients per call. PublicNode returned logs without credentials, but its stable free quota/SLA was not established. Do not increase limits or retry aggressively.

GitHub Actions private repository allowance and storage are plan-dependent; overage may be billed. Current documentation: https://docs.github.com/en/billing/concepts/product-billing/github-actions . The authenticated connector cannot verify owner plan, remaining quota, or spend cap. Daily scheduling remains disabled. Manual workflow has a 15-minute timeout, 10 discovery-page ceiling, 20 MiB database ceiling, 100 MiB reachable blob history ceiling, and concurrency lock.

Evidence branch cross-run state was independently verified at 9d0df92789efaa73f1a7f6fa14fddbfab2a0e3d7; two separate reports contain snapshots 6450af1d-23ca-4873-bc2b-f4d992e65f38 and a6220320-2a6a-4cd9-a75a-51a31e2f68ee.
