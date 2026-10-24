import unittest
from decimal import Decimal
from aie.db import connect

def normalize(base,decimals): return Decimal(base)/(Decimal(10)**decimals)
def hhi(shares): return sum(Decimal(s)**2 for s in shares) if shares else None

class Core(unittest.TestCase):
 def test_schema_and_dedupe(self):
  d=connect(':memory:'); d.execute("INSERT INTO source_observations(source,observed_at,content_hash,raw_json) VALUES('x','t','h','{}')"); d.execute("INSERT OR IGNORE INTO source_observations(source,observed_at,content_hash,raw_json) VALUES('x','t2','h','{}')"); self.assertEqual(d.execute('select count(*) from source_observations').fetchone()[0],1)
 def test_decimal(self): self.assertEqual(normalize('1234567',6),Decimal('1.234567'))
 def test_hhi_empty_is_missing(self): self.assertIsNone(hhi([])); self.assertEqual(hhi([Decimal('.5'),Decimal('.5')]),Decimal('.50'))

if __name__=='__main__': unittest.main()
