# x402 Newcomer Demand Observatory

2026-10-24T19:40:36.802517+00:00

Decision: INSUFFICIENT_DATA

## Discovery
Snapshot 6450af1d-23ca-4873-bc2b-f4d992e65f38: PARTIAL_SNAPSHOT, 1 pages, 100 unique of changing advertised total 40214, next offset 100.
Snapshot a6220320-2a6a-4cd9-a75a-51a31e2f68ee: PARTIAL_SNAPSHOT, 1 pages, 100 unique of changing advertised total 40214, next offset 100.

Partial rotated windows do not establish launch dates or full-catalog coverage.

## Payment evidence: 0 safe/final ledger transfers; 0 token-transfer sender addresses. Merchant match means payTo address match only. Resource calls and buyer independence are unproven.

## Attribution checks: 0 signed-evidence bundles checked; 0 verified resource-attributed purchase records. Missing proof means unavailable, not zero demand.

No cross-asset amount sum or USD peg assumed. Realized LeftSock income: $0.

SQLite integrity: ok.

## Phase VIII: independently reverified Base transfers

The evidence-data branch database used for this report has 2 Bazaar snapshots (100 resources each) and 0 stored payment rows. Separately, two earlier reported Base transactions were re-fetched via the public Base RPC; their decoded evidence is retained at [`reports/evidence/phase-viii-base-transfers.json`](evidence/phase-viii-base-transfers.json). This is not a claim that the transfers were durably stored in the evidence branch before this report.

| Transaction | Event | Token payer (`Transfer.from`) | Recipient | Amount | Block / UTC | Verification |
|---|---:|---|---|---:|---|---|
| [`0xc982c1ae…2b1b40b6`](https://basescan.org/tx/0xc982c1ae9755146fc25e71bb693b9eaf7ea913329894fb6e88253bc42b1b40b6) | 51 | `0x10fd06eb…0fe74458` | `0x058d0cc5…525921b2` | 0.003 USDC | 53,038,428 / 2026-10-24 18:23:23 UTC | successful, safe, block hash matched |
| [`0xe13f1a69…6635558`](https://basescan.org/tx/0xe13f1a69a46a17079227d8fea3e804726187d06f115d8eb5f53164c806635558) | 255 | `0x9d42eba8…f1bbece9` | `0x058d0cc5…525921b2` | 0.003 USDC | 53,038,138 / 2026-10-24 18:13:43 UTC | successful, safe, block hash matched |

The outer transaction senders differ from the token senders in both events. Both transfers match a Bazaar `payTo` address, but the local historical 1,000-resource snapshot contains 18 resources using that address. No evidence connects either event to one endpoint invocation. These are **ledger-confirmed, merchant-associated transfers only**; resource-attributed purchases: 0 verified; independent buyers: unknown; LeftSock realized income: **$0**.

The machine-readable transfer evidence file SHA-256 is `85731920aa699ac76c2b7b0f528225535a7db51debe2ed53b35bf161f59db38c`.

## Attribution finding

The current x402 Foundation optional `offer-receipt` extension supplies a workable method: a signed offer binds a URL and terms; a signed receipt binds URL, payer, network, time, and optional transaction; the transaction can then be matched to the exact token transfer and offer. The report does not treat the optional extension or a seller's signature as independent customer proof. The verifier requires retained signer authorization and fails closed on missing or inconsistent fields. No public mainnet evidence bundle with all these fields was found in the bounded investigation.

The public `x402-receipts` repository includes a real Base transfer in a conformance vector, but its accompanying seller signature is a vector test key and its anchor transaction is explicitly synthetic. It is a software fixture, not an observed resource purchase. Marketplace-reported call or payer counts remain telemetry, not independently verified receipts.

**Economic decision: INSUFFICIENT_DATA.** No category can be ranked as earning resource-attributed receipts from the available verified evidence. Missing request-level evidence is not zero demand. No paid resources were called.

Method and source analysis: [`docs/phase-viii-attribution.md`](../docs/phase-viii-attribution.md).
