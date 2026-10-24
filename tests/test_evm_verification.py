import unittest
from unittest.mock import patch

from aie.evm import CHAIN, TRANSFER, USDC, verify_transaction


TX = "0x" + "12" * 32
BLOCK_HASH = "0x" + "34" * 32
PAYER = "0x" + "56" * 20
PAYTO = "0x" + "78" * 20
OUTER_FROM = "0x" + "9a" * 20


def rpc_fixture(canonical_hash=BLOCK_HASH, safe_number="0x64", receipt_status="0x1"):
    log = {
        "address": USDC,
        "topics": [TRANSFER, "0x" + "0" * 24 + PAYER[2:], "0x" + "0" * 24 + PAYTO[2:]],
        "data": "0xbb8", "logIndex": "0x33", "removed": False,
    }
    receipt = {"transactionHash": TX, "status": receipt_status, "blockNumber": "0x50",
               "blockHash": BLOCK_HASH, "logs": [log]}
    tx = {"hash": TX, "from": OUTER_FROM, "to": USDC}
    block = {"hash": canonical_hash, "timestamp": "0x671a0000"}

    def call(method, params):
        if method == "eth_chainId": return CHAIN
        if method == "eth_getBlockByNumber" and params[0] == "safe": return {"number": safe_number}
        if method == "eth_getTransactionReceipt": return receipt
        if method == "eth_getTransactionByHash": return tx
        if method == "eth_getBlockByNumber": return block
        raise AssertionError((method, params))
    return call


class EvmVerificationTests(unittest.TestCase):
    def test_successful_safe_transfer_separates_outer_sender_and_token_payer(self):
        with patch("aie.evm.rpc", side_effect=rpc_fixture()):
            result = verify_transaction(TX, 51)
        self.assertEqual(result["status"], "LEDGER_CONFIRMED")
        self.assertEqual(result["outer_transaction_from"], OUTER_FROM)
        self.assertEqual(result["transfer"]["from"], PAYER)
        self.assertEqual(result["transfer"]["amount_base"], "3000")
        self.assertEqual(result["amount_normalized"], "0.003")

    def test_reorged_or_mismatched_block_hash_fails(self):
        with patch("aie.evm.rpc", side_effect=rpc_fixture(canonical_hash="0x" + "aa" * 32)):
            with self.assertRaisesRegex(RuntimeError, "block hash"):
                verify_transaction(TX, 51)

    def test_not_yet_safe_transfer_fails_closed(self):
        with patch("aie.evm.rpc", side_effect=rpc_fixture(safe_number="0x40")):
            with self.assertRaisesRegex(RuntimeError, "not at or below the safe block"):
                verify_transaction(TX, 51)

    def test_failed_transaction_receipt_is_rejected(self):
        with patch("aie.evm.rpc", side_effect=rpc_fixture(receipt_status="0x0")):
            with self.assertRaisesRegex(RuntimeError, "did not succeed"):
                verify_transaction(TX, 51)

    def test_wrong_event_index_is_not_silently_accepted(self):
        with patch("aie.evm.rpc", side_effect=rpc_fixture()):
            with self.assertRaisesRegex(RuntimeError, "exactly one"):
                verify_transaction(TX, 52)


if __name__ == "__main__":
    unittest.main()
