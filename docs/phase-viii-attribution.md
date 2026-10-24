# Phase VIII: x402 purchase attribution

## Conclusion

A third-party observer cannot identify an individual resource purchase from public blockchain data alone. Chain data records token movement, not the HTTP request, the resource URL, whether the server delivered a response, or why funds moved. On Base, `Transfer.from` identifies the token payer in the token event; the outer transaction sender can be a relayer and is a separate field.

Resource-level attribution is technically possible when a seller publishes a verifiable x402 signed offer and signed receipt, the receipt names the exact resource URL, payer, network, issue time and transaction hash, the offer signs the resource's exact payment terms, the signer is independently authorized for the resource, and the matching canonical token transfer is successful and final. This is a seller-issued cryptographic attestation joined to ledger evidence. It does not prove that the seller and payer are economically independent, or that the delivered service was useful. The optional offer/receipt extension is not present on every x402 implementation and HTTP response headers are not written to the chain.

## Protocol evidence and proof boundaries

- A `402 Payment Required` challenge exposes off-chain payment requirements (resource, scheme, network, asset, payTo and amount). It proves the server advertised terms, not that anyone paid.
- A client authorization payload proves that a client signed a payment authorization. It is not public merely because it was sent in an HTTP request. ERC-3009 transfers can be submitted by a relayer; the ERC-20 `Transfer.from` is the token payer while the transaction `from` is the relayer.
- A facilitator `SettlementResponse` (`PAYMENT-RESPONSE` for HTTP) reports success, network, payer and transaction hash to the request participants. The response itself is not a public on-chain record and the protocol does not define a public facilitator settlement-history API.
- A canonical ERC-20 `Transfer` event proves exact asset, token sender, recipient, amount and log index. A successful safe/final transaction receipt plus matching block hash establishes ledger evidence, not purchase purpose.
- The current x402 Foundation Offer and Receipt extension is optional. A signed Offer binds resource URL, scheme, network, asset, payTo, amount and optional expiry. A signed Receipt binds network, resource URL, payer, issuedAt and an optional transaction hash; it does not itself bind amount/asset/payTo. The verifier therefore matches both signatures to the same authorized resource signer and checks the receipt's transaction against the exact offer terms and transfer event.
- The offer/receipt signer authorization must be retained separately (for example a resource-controlled DID/DNS authorization record with its bytes, timestamp and hash). A valid signature under an arbitrary key is not enough to prove the key speaks for the resource.
- Even a seller-signed receipt is a seller claim. Buyer countersignature improves evidence of buyer acceptance but cannot establish independent ownership by itself. Independent-buyer corroboration needs separate identity/funding or other external evidence; address count is insufficient.

## Implemented verification

`aie.attribution.verify_purchase` verifies the Foundation EIP-712 v1 Offer and Receipt signatures, explicit resource authorization evidence, exact Base network, receipt transaction and payer, canonical asset/recipient/amount, successful safe/final state, and time/expiry consistency. It returns `RESOURCE_ATTRIBUTED` only when every required input is present and consistent. Unknown or contradictory evidence returns `UNRESOLVED`. It makes no network calls and never promotes an address match. `python -m aie verify-purchase --evidence proof.json` stores a deterministic evidence hash and result in SQLite.

`python -m aie verify-transfer --tx HASH --event-index N` independently fetches one Base transaction from the public read-only RPC and verifies chain id, successful receipt, canonical block hash, safe-block finality and the canonical Base USDC Transfer log. It reports outer transaction sender separately from token payer. This command is bounded to one transaction and does not invoke x402 resources.

This repository has no seller-key authorization records, signed Bazaar/402 offers, signed transaction receipts, facilitator history, or public request/response receipts for its observed transfers. Thus no current record can pass the resource-attribution verifier. Synthetic tests exercise successful logic through an injected signature-recovery test seam; they are expressly not economic evidence. Invalid signatures are tested against the real cryptographic recovery implementation.

## Two historical Base transfers

The two transfers from the Phase VII report were re-fetched on 2026-10-24 using PublicNode. Both are canonical Base USDC (`0x833589...2913`, six decimals), succeeded, and were below safe block 53,040,668 at verification. Each is 3,000 base units (0.003 USDC) to the same recipient. Their transaction senders differ from their ERC-20 `Transfer.from` payer addresses. The complete decoded response and matching Bazaar metadata hashes are retained in `reports/evidence/phase-viii-base-transfers.json`.

The corresponding local discovery snapshot contains 18 Bazaar resources with that same `payTo` address. A single transfer cannot be assigned among those endpoints without a resource receipt or an equivalent independently retained request-level record. The durable `evidence-data` branch's SQLite copy holds two Bazaar snapshots and zero payment rows; the new JSON evidence record is the durable, hashable record of this bounded re-verification. None of the two movements is claimed to be an x402 purchase or a LeftSock receipt.

## Public candidate investigation

The x402 Foundation's specification provides the appropriate attribution mechanism but treats it as an optional extension; its illustrative transaction hashes/signatures are examples, not real purchase evidence. The public `x402-receipts` repository publishes a settlement test vector using a real Base USDC transfer, but explicitly labels the seller receipt as test-key data and its anchor transaction as synthetic; it is a conformance fixture, not evidence that the transfer bought the referenced resource. Bazaar/third-party directory activity counts remain marketplace telemetry and do not expose the underlying signed resource receipts.

No independently corroborated, real mainnet x402 purchase with a public transaction, signed resource-bound receipt, verified signer authorization and matching signed terms was found in the bounded investigation. No paid endpoints were called.

## Smallest evidence that changes the result

One resource operator should publish, without requiring payment, a signed evidence bundle containing: (1) the contemporaneous signed Offer from its `PAYMENT-REQUIRED` response, (2) a signed Receipt with a non-empty transaction hash, (3) the public authorization record for the signer scoped to that resource, and (4) a reproducible link to the successful finalized transaction/log. A third party can then verify the seller-attributed resource purchase without making a purchase. To support independent-buyer confidence, the bundle additionally needs a buyer countersignature and independent corroboration that the payer is not controlled by the seller. No such public bundle was available for the present observations.

## References

- [x402 v2 core specification](https://github.com/x402-foundation/x402/blob/main/specs/x402-specification-v2.md)
- [x402 HTTP transport specification](https://github.com/x402-foundation/x402/blob/main/specs/transports-v2/http.md)
- [Offer and Receipt extension specification](https://github.com/x402-foundation/x402/blob/main/specs/extensions/extension-offer-and-receipt.md)
- [Coinbase Bazaar resource discovery documentation](https://docs.cdp.coinbase.com/api-reference/v2/rest-api/x402-facilitator/browse-the-catalog)
- [x402-receipts test vector and explicit trust limits](https://github.com/StelarDigital/x402-receipts/tree/main/vectors)
- [Base public RPC](https://base-rpc.publicnode.com)
