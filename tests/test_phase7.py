import unittest
from decimal import Decimal
from unittest.mock import patch
from aie.db import connect
from aie.analysis import payer_metrics,token_amount
from aie.evm import collect,CHAIN,USDC,TRANSFER
from aie.discovery import scan
class Phase7(unittest.TestCase):
 def test_count_vs_value_concentration(self):
  m=payer_metrics([{'payer':'a','day':'d','tx_id':'1','amount':'99'},{'payer':'b','day':'d','tx_id':'2','amount':'1'}])['inclusive']
  self.assertEqual(m['payment_count_hhi'],Decimal('.5'));self.assertGreater(m['payment_value_hhi'],Decimal('.98'))
 def test_token_base_units(self):self.assertEqual(token_amount('3000',6),Decimal('.003'))
 def test_incomplete_scan_remains_partial(self):
  d=connect(':memory:');_,s=scan(d,1,1,fetcher=lambda o,l:{'items':[{'id':'r'}],'pagination':{'total':200}});self.assertEqual(s,'PARTIAL_SNAPSHOT')
 def test_identical_payload_creates_distinct_snapshot_records(self):
  d=connect(':memory:');p={'items':[{'id':'same'}],'pagination':{'total':1}};a,_=scan(d,1,2,fetcher=lambda o,l:p);b,_=scan(d,1,2,fetcher=lambda o,l:p);self.assertNotEqual(a,b);self.assertEqual(d.execute('select count(*) from resource_observations').fetchone()[0],2)
 def test_transfer_deduplicates_address_match_only(self):
  d=connect(':memory:');d.execute("insert into discovery_snapshots(id,started_at,status,page_size,max_pages) values('s','t','PARTIAL_SNAPSHOT',1,1)");d.execute("insert into resource_observations values('s','r','t','h',?)",('{"accepts":[{"payTo":"0x'+'11'*20+'"}]}',))
  log={'address':USDC,'topics':[TRANSFER,'0x'+'0'*24+'22'*20,'0x'+'0'*24+'11'*20],'data':'0x2ee0','transactionHash':'0x'+'33'*32,'logIndex':'0x1','blockNumber':'0x10','blockHash':'0x'+'44'*32,'removed':False}
  def rpc(m,p):
   if m=='eth_chainId':return CHAIN
   if m=='eth_getBlockByNumber' and p[0]=='safe':return {'number':'0x20','timestamp':'0x65a00000'}
   if m=='eth_getBlockByNumber':return {'timestamp':'0x65a00000'}
   if m=='eth_getLogs':return [log,log]
  with patch('aie.evm.rpc',side_effect=rpc):collect(d,20)
  with patch('aie.evm.rpc',side_effect=rpc):collect(d,20)
  self.assertEqual(d.execute('select count(*) from payments').fetchone()[0],1)
  self.assertEqual(d.execute('select amount_normalized,finality from payments').fetchone(),('0.012','SAFE'))
  self.assertEqual(d.execute('select level from payment_attributions').fetchone()[0],'MERCHANT_ASSOCIATED')
 def test_unsupported_token_not_ingested(self):
  d=connect(':memory:');d.execute("insert into discovery_snapshots(id,started_at,status,page_size,max_pages) values('s','t','PARTIAL_SNAPSHOT',1,1)");d.execute("insert into resource_observations values('s','r','t','h',?)",('{"accepts":[{"payTo":"0x'+'11'*20+'"}]}',))
  log={'address':'0x'+'99'*20,'topics':[TRANSFER,'0x'+'0'*64,'0x'+'0'*64],'data':'0x1','transactionHash':'0x'+'22'*32,'logIndex':'0x1','blockNumber':'0x10','removed':False}
  def rpc(m,p):
   if m=='eth_chainId':return CHAIN
   if m=='eth_getBlockByNumber':return {'number':'0x20','timestamp':'0x65a00000'}
   if m=='eth_getLogs':return [log]
  with patch('aie.evm.rpc',side_effect=rpc):collect(d,20)
  self.assertEqual(d.execute('select count(*) from payments').fetchone()[0],0)
if __name__=='__main__':unittest.main()
