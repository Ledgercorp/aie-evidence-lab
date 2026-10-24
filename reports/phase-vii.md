# AIE Evidence Lab Phase VII Report
Generated 2026-10-24 UTC. Decision: **INSUFFICIENT_DATA**.

## Discovery
The live local scan retained 1,000 unique resources across 10 pages against advertised 40,036. It is partial and biased by deterministic offset order. The new cursor rotates offsets across runs; catalog reorderings may still create overlap or gaps. Unseen resources are not classified as new launches.

## Settlement evidence
Base chain ID 8453 and PublicNode JSON-RPC were verified. A bounded scan of safe-tag blocks 53037944–53038443 checked 25 published payTo addresses and retained two canonical Base USDC Transfer events:
- tx 0xc982c1ae9755146fc25e71bb693b9eaf7ea913329894fb6e88253bc42b1b40b6, block 53038428, 3,000 base units = 0.003 USDC.
- tx 0xe13f1a69a46a17079227d8fea3e804726187d06f115d8eb5f53164c806635558, block 53038138, 3,000 base units = 0.003 USDC.

Both recipients matched the same published payTo address. Classification: ledger confirmed and merchant associated by address match only. They do not prove an x402 invocation, independent customers, or resource-level revenue. Nominal 0.006 USDC is not LeftSock income. Realized LeftSock income: $0.

## Operations
Two separate prior GitHub Actions runs persisted snapshots 6450af1d-23ca-4873-bc2b-f4d992e65f38 and a6220320-2a6a-4cd9-a75a-51a31e2f68ee to evidence-data; the second report restored both. The current manual workflow adds database and reachable blob-size caps. GitHub billing docs are plan-dependent and overage is billable; account plan/quota/spend-cap were not available to inspect, so daily scheduling remains disabled.

No endpoint-level attribution or commercial demand conclusion is supported.