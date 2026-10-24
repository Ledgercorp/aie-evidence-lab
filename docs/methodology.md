# Methodology

Every discovery response is retained in `source_observations` with retrieval time and SHA-256. Stable resource IDs are used when supplied; otherwise a hash of the metadata serves as a snapshot-local identity and must not be interpreted as merchant identity. Snapshots preserve changes. Payment records require chain, transaction and event identifiers; attribution rows separately encode merchant/resource and evidence level. The present build has no chain adapter, so it reports unavailable rather than zero verified market activity.

Bootstrap exclusion requires an identifiable first payment. Until settlement evidence exists, bootstrap and recurrent demand metrics remain unavailable. Cohorts must be treated as right-censored until their requested follow-up window elapses. Economic scenarios are arithmetic estimates and are not demand evidence.
