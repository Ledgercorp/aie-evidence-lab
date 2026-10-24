from collections import defaultdict
from decimal import Decimal
def payer_metrics(payments,bootstrap_tx=None):
 rows=sorted(payments,key=lambda r:(r['day'],r['tx_id']));post=[r for r in rows if r['tx_id']!=bootstrap_tx] if bootstrap_tx else rows[1:]
 def summary(xs):
  counts=defaultdict(int);values=defaultdict(Decimal);days=defaultdict(set)
  for r in xs:counts[r['payer']]+=1;values[r['payer']]+=Decimal(r['amount']);days[r['payer']].add(r['day'])
  def hhi(d):
   total=sum(d.values(),Decimal(0));return sum((v/total)**2 for v in d.values()) if total else None
  return {'payments':len(xs),'distinct_payer_addresses':len(counts),'repeat_payer_addresses':sum(len(v)>1 for v in days.values()),'gross_observed_value':sum(values.values(),Decimal(0)),'payment_count_hhi':hhi({k:Decimal(v) for k,v in counts.items()}),'payment_value_hhi':hhi(values)}
 return {'inclusive':summary(rows),'post_bootstrap':summary(post),'bootstrap_status':'KNOWN' if bootstrap_tx else ('UNKNOWN_EARLIEST_EXCLUDED_IN_POST_VIEW' if rows else 'NO_PAYMENTS'),'payer_independence':'NOT_ESTABLISHED'}
