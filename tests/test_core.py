import unittest
from decimal import Decimal
from datetime import date
from aie.db import connect
from aie.analysis import token_amount, payer_metrics, cohort_status, time_to_nth_distinct_payer

def normalize(base,decimals): return Decimal(base)/(Decimal(10)**decimals)
def hhi(shares): return sum(Decimal(s)**2 for s in shares) if shares else None

class Core(unittest.TestCase):
 def test_schema_and_dedupe(self):
  d=connect(':memory:'); d.execute("INSERT INTO source_observations(source,observed_at,content_hash,raw_json) VALUES('x','t','h','{}')"); d.execute("INSERT OR IGNORE INTO source_observations(source,observed_at,content_hash,raw_json) VALUES('x','t2','h','{}')"); self.assertEqual(d.execute('select count(*) from source_observations').fetchone()[0],1)
 def test_decimal(self): self.assertEqual(normalize('1234567',6),Decimal('1.234567'))
 def test_hhi_empty_is_missing(self): self.assertIsNone(hhi([])); self.assertEqual(hhi([Decimal('.5'),Decimal('.5')]),Decimal('.50'))
 def test_token_decimal_precision(self): self.assertEqual(token_amount('1000001',6),Decimal('1.000001'))
 def test_negative_decimals_rejected(self):
  with self.assertRaises(ValueError): token_amount('1',-1)
 def test_unknown_bootstrap_excludes_earliest_only_in_secondary_view(self):
  rows=[{'payer':'a','day':'2026-01-01','amount':'1','tx_id':'1'},{'payer':'b','day':'2026-01-02','amount':'2','tx_id':'2'}]
  m=payer_metrics(rows); self.assertEqual(m['inclusive']['payment_count'],2); self.assertEqual(m['post_bootstrap']['payment_count'],1); self.assertEqual(m['bootstrap_status'],'UNKNOWN_EARLIEST_EXCLUDED_IN_POST_VIEW')
 def test_repeat_payer_is_address_observation(self):
  rows=[{'payer':'a','day':'2026-01-01','amount':'1','tx_id':'1'},{'payer':'a','day':'2026-01-02','amount':'1','tx_id':'2'},{'payer':'b','day':'2026-01-02','amount':'2','tx_id':'3'}]
  m=payer_metrics(rows)['inclusive']; self.assertEqual(m['repeat_payer_addresses'],1); self.assertEqual(m['distinct_payer_addresses'],2); self.assertEqual(m['payer_hhi'],Decimal('0.5555555555555555555555555556'))
 def test_no_data_is_missing(self):
  m=payer_metrics([])['inclusive']; self.assertIsNone(m['payer_hhi']); self.assertIsNone(m['median_payment']); self.assertEqual(m['gross_observed_value'],Decimal(0))
 def test_cohort_right_censor(self): self.assertTrue(cohort_status(date(2026,1,1),date(2026,1,10),14)['censored']); self.assertFalse(cohort_status(date(2026,1,1),date(2026,1,20),14)['censored'])
 def test_time_to_second_distinct_address(self):
  rows=[{'payer':'a','day':'2026-01-01','tx_id':'1'},{'payer':'a','day':'2026-01-02','tx_id':'2'},{'payer':'b','day':'2026-01-03','tx_id':'3'}]
  self.assertEqual(time_to_nth_distinct_payer(rows,2),'2026-01-03'); self.assertIsNone(time_to_nth_distinct_payer(rows,4))
 def test_multiple_addresses_not_independent_customers(self):
  rows=[{'payer':'x','day':'2026-01-01','amount':'1','tx_id':'1'},{'payer':'y','day':'2026-01-02','amount':'1','tx_id':'2'}]
  self.assertEqual(payer_metrics(rows)['payer_independence'],'NOT_ESTABLISHED')

if __name__=='__main__': unittest.main()
