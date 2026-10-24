import unittest
from decimal import Decimal
from datetime import date
from aie.db import connect
from aie.analysis import token_amount,payer_metrics,cohort_status,time_to_nth_distinct_payer
from aie.discovery import scan
from aie.economics import required_calls
class Core(unittest.TestCase):
 def test_db_dedup(self):
  d=connect(':memory:');d.execute("insert into source_observations values(null,'x','1','h','{}')");d.execute("insert or ignore into source_observations values(null,'x','2','h','{}')");self.assertEqual(d.execute('select count(*) from source_observations').fetchone()[0],1)
 def test_decimal(self):self.assertEqual(token_amount('1000001',6),Decimal('1.000001'))
 def test_empty_metrics(self):self.assertIsNone(payer_metrics([])['inclusive']['payer_hhi'])
 def test_bootstrap_views(self):
  m=payer_metrics([{'payer':'a','day':'1','amount':'1','tx_id':'1'},{'payer':'b','day':'2','amount':'2','tx_id':'2'}]);self.assertEqual(m['post_bootstrap']['payment_count'],1)
 def test_address_repeat(self):
  m=payer_metrics([{'payer':'a','day':'1','amount':'1','tx_id':'1'},{'payer':'a','day':'2','amount':'1','tx_id':'2'}]);self.assertEqual(m['inclusive']['repeat_payer_addresses'],1);self.assertEqual(m['payer_independence'],'NOT_ESTABLISHED')
 def test_censor(self):self.assertTrue(cohort_status(date(2026,1,1),date(2026,1,2),14)['censored'])
 def test_nth_payer(self):self.assertEqual(time_to_nth_distinct_payer([{'payer':'a','day':'1','tx_id':'1'},{'payer':'b','day':'2','tx_id':'2'}],2),'2')
 def test_pages_complete(self):
  d=connect(':memory:');q={0:{'items':[{'id':'a'},{'id':'b'}],'pagination':{'total':3}},2:{'items':[{'id':'c'}],'pagination':{'total':3}}};sid,s=scan(d,2,2,fetcher=lambda o,l:q[o]);self.assertEqual(s,'COMPLETE_SNAPSHOT')
 def test_pages_partial(self):
  d=connect(':memory:');_,s=scan(d,1,1,fetcher=lambda o,l:{'items':[{'id':'a'}],'pagination':{'total':5}});self.assertEqual(s,'PARTIAL_SNAPSHOT')
 def test_repeat_page_partial(self):
  d=connect(':memory:');q={'items':[{'id':'a'}],'pagination':{'total':5}};_,s=scan(d,4,1,fetcher=lambda o,l:q);self.assertEqual(s,'PARTIAL_SNAPSHOT')
 def test_same_resource_snapshots(self):
  d=connect(':memory:');q={'items':[{'id':'a'}],'pagination':{'total':1}};a,_=scan(d,1,2,fetcher=lambda o,l:q);b,_=scan(d,1,2,fetcher=lambda o,l:q);self.assertNotEqual(a,b);self.assertEqual(d.execute('select count(*) from resource_observations').fetchone()[0],2)
 def test_resume(self):
  d=connect(':memory:');sid,_=scan(d,1,1,fetcher=lambda o,l:{'items':[{'id':str(o)}],'pagination':{'total':3}});_,s=scan(d,3,1,snapshot_id=sid,fetcher=lambda o,l:{'items':[{'id':str(o)}],'pagination':{'total':3}});self.assertEqual(s,'COMPLETE_SNAPSHOT')
 def test_economics(self):self.assertEqual(required_calls('1','0.05',marginal_cost='0.01'),25);self.assertIsNone(required_calls('1','0.05',marginal_cost='0.06'))
if __name__=='__main__':unittest.main()
