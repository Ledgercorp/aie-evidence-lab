from collections import defaultdict
from datetime import date
from decimal import Decimal
def token_amount(base_units,decimals):
 if decimals<0:raise ValueError('decimals must be non-negative')
 return Decimal(base_units)/(Decimal(10)**decimals)
def payer_metrics(payments,bootstrap_tx=None):
 rows=sorted(payments,key=lambda r:(r['day'],r['tx_id']));post=[r for r in rows if r['tx_id']!=bootstrap_tx] if bootstrap_tx else rows[1:]
 def summary(xs):
  counts=defaultdict(int);values=defaultdict(Decimal);days=defaultdict(set)
  for r in xs:counts[r['payer']]+=1;values[r['payer']]+=Decimal(r['amount']);days[r['payer']].add(r['day'])
  def hhi(d):
   total=sum(d.values(),Decimal(0));return sum((v/total)**2 for v in d.values()) if total else None
  ch=hhi({k:Decimal(v) for k,v in counts.items()})
  return {'payments':len(xs),'payment_count':len(xs),'distinct_payer_addresses':len(counts),'repeat_payer_addresses':sum(len(v)>1 for v in days.values()),'gross_observed_value':sum(values.values(),Decimal(0)),'payer_hhi':ch,'payment_count_hhi':ch,'payment_value_hhi':hhi(values),'median_payment':None}
 return {'inclusive':summary(rows),'post_bootstrap':summary(post),'bootstrap_status':'KNOWN' if bootstrap_tx else ('UNKNOWN_EARLIEST_EXCLUDED_IN_POST_VIEW' if rows else 'NO_PAYMENTS'),'payer_independence':'NOT_ESTABLISHED'}
def cohort_status(first_seen,as_of,window_days):
 elapsed=max(0,(as_of-first_seen).days);return {'observation_days':elapsed,'censored':elapsed<window_days,'window_days':window_days}
def time_to_nth_distinct_payer(rows,n):
 if n<1:raise ValueError('n must be positive')
 seen=set()
 for r in sorted(rows,key=lambda x:(x['day'],x['tx_id'])):
  seen.add(r['payer'])
  if len(seen)>=n:return r['day']
 return None
