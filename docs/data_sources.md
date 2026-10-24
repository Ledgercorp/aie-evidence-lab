# Sources and verification

As of 2026-10-24, a read-only GET to `https://api.cdp.coinbase.com/platform/v2/x402/discovery/resources` returned JSON with an `items` array and resource fields including `accepts[].network`, `payTo`, `asset`, `amount`, plus descriptions. The CLI stores complete response evidence by content hash. No page token or stable pagination contract was confirmed; therefore collection currently requests one page only.

Official docs entry point: https://docs.cdp.coinbase.com/x402/bazaar/overview . The direct docs page returned an application error during this run; endpoint response itself was live verified but does not establish official guarantees. Settlement sources, Base RPC, Solana RPC and analytics sources were not verified and remain unavailable/unimplemented.

HTTP 402 is treated as a hard stop. The collector never contacts advertised resource endpoints.
