"""Conservative deterministic metrics over normalized payment records."""
from collections import defaultdict
from datetime import date
from decimal import Decimal

def token_amount(base_units: str, decimals: int) -> Decimal:
    if decimals < 0:
        raise ValueError('decimals must be non-negative')
    return Decimal(base_units) / (Decimal(10) ** decimals)

def payer_metrics(payments, bootstrap_tx=None):
    """Rows use payer/day/amount/tx_id; address counts are not customer counts."""
    ordered=sorted(payments,key=lambda x:(x['day'],x['tx_id']))
    inclusive=_summarize(ordered)
    post=[p for p in ordered if p['tx_id'] != bootstrap_tx] if bootstrap_tx else ordered[1:]
    return {'inclusive':inclusive,'post_bootstrap':_summarize(post),
            'bootstrap_status':'KNOWN' if bootstrap_tx else ('UNKNOWN_EARLIEST_EXCLUDED_IN_POST_VIEW' if ordered else 'NO_PAYMENTS'),
            'payer_independence':'NOT_ESTABLISHED'}

def _summarize(rows):
    payers={r['payer'] for r in rows}; days=defaultdict(set); amounts=[]
    for r in rows:
        days[r['payer']].add(r['day']); amounts.append(Decimal(r['amount']))
    daily=defaultdict(Decimal)
    for r in rows: daily[r['day']]+=Decimal(r['amount'])
    vals=sorted(amounts)
    def median(xs):
        if not xs:return None
        n=len(xs); return xs[n//2] if n%2 else (xs[n//2-1]+xs[n//2])/2
    shares=[Decimal(sum(r['payer']==payer for r in rows))/len(rows) for payer in payers] if rows else []
    return {'payment_count':len(rows),'distinct_payer_addresses':len(payers),
        'repeat_payer_addresses':sum(1 for d in days.values() if len(d)>1),
        'gross_observed_value':sum(amounts,Decimal(0)), 'median_payment':median(vals),
        'median_daily_payment_count':median([Decimal(sum(r['day']==day for r in rows)) for day in sorted(daily)]),
        'attributed_payment_count':sum(bool(r.get('attributed')) for r in rows),
        'unattributed_payment_count':sum(not bool(r.get('attributed')) for r in rows),
        'payer_hhi':sum((s*s for s in shares),Decimal(0)) if shares else None}

def cohort_status(first_seen: date, as_of: date, window_days: int):
    elapsed=max(0,(as_of-first_seen).days)
    return {'observation_days':elapsed,'censored':elapsed<window_days,'window_days':window_days}

def time_to_nth_distinct_payer(payments, n):
    if n<1: raise ValueError('n must be positive')
    seen=set()
    for row in sorted(payments,key=lambda r:(r['day'],r['tx_id'])):
        seen.add(row['payer'])
        if len(seen)>=n:return row['day']
    return None
