# AIE Evidence Lab Phase VII Report

Generated 2026-10-24 (UTC). Decision: **INSUFFICIENT_DATA**.

## Discovery
The retained local live scan covers 1,000 unique resources over 10 pages of requested size 100, against an advertised 40,036. It is partial and is not representative of the full catalog. Catalog totals changed between observations. The latest code rotates deterministic sequential offset windows across executions; ordering shifts remain a sampling limitation. First observed does not mean newly launched.

## Payment evidence
A bounded read-only Base RPC collection checked chain 8453, canonical Base USDC contract 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913, and safe-tag blocks. Two transfer events were retained in the 500-block window for 25 observed payTo addresses. Each amount was 3,000 base units (0.003 USDC); both recipients matched a published payTo address. Transactions:
- 0xc982c1ae9755146fc25e71bb693b9eaf7ea913329894fb6e88253bc42b1b40b6 (block 53038428)
- 0xe13f1a69a46a17079227d8fea3e804726187d06f115d8eb5f53164c806635558 (block 53038138)

Classification: ledger-confirmed; merchant-associated by address match. This does not establish an x402 invocation, independent buyers, or resource-level revenue. 0.006 USDC is competitor/merchant-associated transfer value, never LeftSock income. Realized LeftSock income is $0.

## Limits and decision
PublicNode returned actual logs, but no documented no-cost quota/SLA was verified. Requests are limited to 500 safe blocks and 25 seller addresses. Earlier Base RPC and Blockscout probes returned 429 and 403 respectively. GitHub billing docs list plan-dependent free minutes/storage and bill overages. Owner plan and remaining quota are unavailable, so daily schedule remains disabled. Cross-run persistence was independently verified in the evidence branch before this phase. Demand measurement remains insufficient.
