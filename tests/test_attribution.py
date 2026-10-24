"""Synthetic adversarial fixtures; none of these represent observed purchases."""
import copy
import unittest
from unittest.mock import patch

from aie.attribution import verify_purchase
from aie.attribution import store_verification
from aie.db import connect


SYNTHETIC_SIGNER = "0x" + "ab" * 20
TX = "0x" + "12" * 32
PAYER = "0x" + "34" * 20
PAYTO = "0x" + "56" * 20
USDC = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"


def fixture():
    return {
        "resource": {"id": "synthetic-resource-1", "resource_url": "https://example.invalid/data", "pay_to": PAYTO},
        "offer": {
            "format": "eip712", "payload": {
                "version": 1, "resourceUrl": "https://example.invalid/data", "scheme": "exact",
                "network": "eip155:8453", "asset": USDC, "payTo": PAYTO,
                "amount": "3000", "validUntil": 1792870000,
            }, "signature": "0x" + "11" * 65,
        },
        "receipt": {
            "format": "eip712", "payload": {
                "version": 1, "network": "eip155:8453", "resourceUrl": "https://example.invalid/data",
                "payer": PAYER, "issuedAt": 1792866203, "transaction": TX,
            }, "signature": "0x" + "22" * 65,
        },
        "authorization": {
            "resource_url": "https://example.invalid/data", "signer": SYNTHETIC_SIGNER,
            "evidence_ref": "synthetic://authorization-fixture", "verified": True,
            "evidence": {"resource_url": "https://example.invalid/data", "signer": SYNTHETIC_SIGNER, "label": "SYNTHETIC"},
        },
        "settlement": {
            "chain_id": 8453, "transaction_hash": TX, "log_index": 51,
            "status": "LEDGER_CONFIRMED", "receipt_status": "SUCCESS", "block_hash": "0x" + "90" * 32,
            "source_ref": "synthetic://verified-base-transfer", "block_time": "2026-10-24T18:23:23+00:00", "finality": "SAFE",
            "outer_transaction_from": "0x" + "78" * 20,
            "transfer": {"log_index": 51, "from": PAYER, "to": PAYTO, "asset": USDC, "amount_base": "3000"},
        },
    }


class AttributionTests(unittest.TestCase):
    def run_valid_fixture(self, evidence):
        with patch("aie.attribution.recover_signer", return_value=SYNTHETIC_SIGNER):
            return verify_purchase(evidence)

    def test_consistent_synthetic_signed_evidence_reaches_resource_level(self):
        result = self.run_valid_fixture(fixture())
        self.assertEqual(result["classification"], "RESOURCE_ATTRIBUTED")
        self.assertEqual(result["independent_buyer"], "NOT_ESTABLISHED")

    def test_outer_transaction_sender_is_not_assumed_to_be_token_payer(self):
        evidence = fixture()
        evidence["settlement"]["outer_transaction_from"] = "0x" + "99" * 20
        self.assertEqual(self.run_valid_fixture(evidence)["classification"], "RESOURCE_ATTRIBUTED")

    def test_ordinary_transfer_without_signed_resource_receipt_is_unresolved(self):
        evidence = fixture()
        evidence["receipt"] = {}
        result = verify_purchase(evidence)
        self.assertEqual(result["classification"], "UNRESOLVED")
        self.assertTrue(any("receipt signature" in x for x in result["contradictions"]))

    def test_wrong_token_contract_is_not_a_purchase(self):
        evidence = fixture()
        evidence["settlement"]["transfer"]["asset"] = "0x" + "99" * 20
        self.assertIn("settlement asset does not match signed x402 evidence", self.run_valid_fixture(evidence)["contradictions"])

    def test_bazaar_resource_recipient_must_match_the_signed_offer(self):
        evidence = fixture()
        evidence["resource"]["pay_to"] = "0x" + "99" * 20
        self.assertIn("signed offer recipient does not match the retained Bazaar resource", self.run_valid_fixture(evidence)["contradictions"])

    def test_unapproved_token_cannot_become_a_purchase_even_if_offer_matches(self):
        evidence = fixture()
        evidence["offer"]["payload"]["asset"] = "0x" + "99" * 20
        evidence["settlement"]["transfer"]["asset"] = "0x" + "99" * 20
        self.assertIn("signed offer does not use the approved canonical Base USDC contract", self.run_valid_fixture(evidence)["contradictions"])

    def test_token_base_unit_amount_must_match_signed_offer(self):
        evidence = fixture()
        evidence["settlement"]["transfer"]["amount_base"] = "3000000"
        self.assertIn("settlement base-unit amount does not match signed x402 evidence", self.run_valid_fixture(evidence)["contradictions"])

    def test_mismatched_resource_url_fails_closed(self):
        evidence = fixture()
        evidence["receipt"]["payload"]["resourceUrl"] = "https://example.invalid/other"
        result = self.run_valid_fixture(evidence)
        self.assertIn("signed receipt resource URL does not match expected Bazaar resource", result["contradictions"])

    def test_mismatched_transaction_hash_fails_closed(self):
        evidence = fixture()
        evidence["receipt"]["payload"]["transaction"] = "0x" + "ef" * 32
        self.assertIn("signed receipt transaction hash does not match verified settlement", self.run_valid_fixture(evidence)["contradictions"])

    def test_nonfinal_settlement_is_not_attributable(self):
        evidence = fixture()
        evidence["settlement"]["finality"] = "PENDING"
        result = self.run_valid_fixture(evidence)
        self.assertEqual(result["classification"], "UNRESOLVED")
        self.assertIn("safe/final transaction status", result["missing_evidence"])

    def test_unverified_chain_bundle_is_not_attributable(self):
        evidence = fixture()
        evidence["settlement"]["status"] = "UNRESOLVED"
        result = self.run_valid_fixture(evidence)
        self.assertEqual(result["classification"], "UNRESOLVED")
        self.assertIn("ledger collector status LEDGER_CONFIRMED", result["missing_evidence"])

    def test_malformed_evidence_sections_fail_closed_without_crashing(self):
        evidence = fixture()
        evidence["settlement"] = ["not", "an", "object"]
        result = verify_purchase(evidence)
        self.assertEqual(result["classification"], "UNRESOLVED")
        self.assertIn("settlement evidence must be a JSON object", result["contradictions"])

    def test_malformed_chain_id_fails_closed_without_crashing(self):
        evidence = fixture()
        evidence["settlement"]["chain_id"] = "not-a-chain"
        result = self.run_valid_fixture(evidence)
        self.assertEqual(result["classification"], "UNRESOLVED")
        self.assertIn("settlement chain ID is not Base mainnet 8453", result["contradictions"])

    def test_malformed_transfer_object_fails_closed_without_crashing(self):
        evidence = fixture()
        evidence["settlement"]["transfer"] = "not-a-transfer-object"
        result = self.run_valid_fixture(evidence)
        self.assertEqual(result["classification"], "UNRESOLVED")
        self.assertIn("settlement transfer evidence must be a JSON object", result["contradictions"])

    def test_missing_resource_signer_authorization_is_unknown(self):
        evidence = fixture()
        evidence["authorization"] = {"signer": SYNTHETIC_SIGNER}
        result = self.run_valid_fixture(evidence)
        self.assertEqual(result["classification"], "UNRESOLVED")
        self.assertIn("retained resource-to-signing-key authorization evidence", result["missing_evidence"])

    def test_unreviewed_authorization_reference_is_not_treated_as_verified(self):
        evidence = fixture()
        evidence["authorization"]["verified"] = False
        result = self.run_valid_fixture(evidence)
        self.assertEqual(result["classification"], "UNRESOLVED")
        self.assertIn("independently reviewed resource signer authorization", result["missing_evidence"])

    def test_authorization_must_be_valid_at_the_receipt_time(self):
        evidence = fixture()
        evidence["authorization"]["valid_until"] = 1792860000
        self.assertIn("resource signer authorization had expired at receipt time", self.run_valid_fixture(evidence)["contradictions"])

    def test_expired_offer_contradiction_is_retained(self):
        evidence = fixture()
        evidence["offer"]["payload"]["validUntil"] = 1790000000
        self.assertIn("signed offer expired before settlement", self.run_valid_fixture(evidence)["contradictions"])

    def test_invalid_real_signature_stays_unresolved(self):
        evidence = fixture()
        evidence["offer"]["signature"] = "0x" + "00" * 65
        result = verify_purchase(evidence)
        self.assertEqual(result["classification"], "UNRESOLVED")
        self.assertFalse(result["signatures"]["offer_valid"])

    def test_address_match_without_resource_evidence_does_not_promote(self):
        evidence = fixture()
        evidence["authorization"]["resource_url"] = "https://example.invalid/other"
        result = self.run_valid_fixture(evidence)
        self.assertEqual(result["classification"], "UNRESOLVED")
        self.assertIn("signer authorization applies to a different resource URL", result["contradictions"])

    def test_repeat_verification_has_stable_evidence_hash(self):
        evidence = fixture()
        first = self.run_valid_fixture(evidence)
        second = self.run_valid_fixture(copy.deepcopy(evidence))
        self.assertEqual(first["evidence_hash"], second["evidence_hash"])

    def test_idempotent_storage_retains_raw_evidence_and_result(self):
        evidence = fixture()
        result = self.run_valid_fixture(evidence)
        db = connect(":memory:")
        store_verification(db, evidence, result)
        store_verification(db, evidence, result)
        row = db.execute("select evidence_json,result_json from payment_attribution_checks").fetchone()
        self.assertEqual(db.execute("select count(*) from payment_attribution_checks").fetchone()[0], 1)
        self.assertIn("synthetic", row[0])
        self.assertIn("RESOURCE_ATTRIBUTED", row[1])


if __name__ == "__main__":
    unittest.main()
