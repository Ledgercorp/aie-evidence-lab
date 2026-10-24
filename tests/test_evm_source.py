import unittest
from aie.evm import CHAIN,USDC,TRANSFER
class SettlementSourceTests(unittest.TestCase):
 def test_chain_is_base(self):self.assertEqual(CHAIN,'0x2105')
 def test_stablecoin_contract_is_canonical_base_usdc(self):self.assertEqual(USDC,'0x833589fcd6edb6e08f4c7c32d4f71b54bda02913')
 def test_transfer_topic_is_erc20_transfer(self):self.assertEqual(len(TRANSFER),66)
