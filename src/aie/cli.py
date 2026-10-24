import argparse, hashlib, json, os, sqlite3, sys, urllib.request, urllib.error
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from .db import connect

URL='https://api.cdp.coinbase.com/platform/v2/x402/discovery/resources'
UA='LeftSock-AIE-Evidence-Lab/0.1 (read-only research)'
MANIFEST={"bazaar":{"status":"VERIFIED_LIVE","url":URL,"auth":"none observed","notes":"limit/offset and pagination.total verified; scans are bounded by --max-pages"},"settlements":{"status":"AVAILABLE_WITH_LIMITATIONS","notes":"No unauthenticated, durable, provider-independent Base log source established; no live settlement ingestion"},"base_rpc":{"status":"AVAILABLE_WITH_LIMITATIONS","notes":"Base JSON-RPC eth_getLogs requires a provider endpoint; public endpoints are rate limited and historical coverage varies"},"solana":{"status":"NOT_IMPLEMENTED"},"telemetry":{"status":"AVAILABLE_WITH_LIMITATIONS","notes":"Bazaar quality telemetry is marketplace-reported, not settlement evidence"}}

def request(url=URL,timeout=15):
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'application/json'})
    with urllib.request.urlopen(req,timeout=timeout) as resp:
        if resp.status==402: raise RuntimeError('HTTP 402; payment prohibited; no retry')
        return json.load(resp)

def collect(db,fixture=False,max_pages=5,page_size=100):
    start=datetime.now(timezone.utc).isoformat(); seen={}; pages=0; total=None
    while pages < max_pages:
        offset=pages*page_size
        payload=json.loads(Path(fixture).read_text()) if fixture else request(f'{URL}?limit={page_size}&offset={offset}')
        items=payload.get('items',[]) if isinstance(payload,dict) else []
        if not isinstance(items,list): raise ValueError('Expected items array')
        pagination=payload.get('pagination') or {}; total=pagination.get('total',total)
        now=datetime.now(timezone.utc).isoformat(); raw=json.dumps(payload,sort_keys=True,separators=(',',':')); digest=hashlib.sha256(raw.encode()).hexdigest()
        cur=db.execute('INSERT OR IGNORE INTO source_observations(source,observed_at,content_hash,raw_json) VALUES(?,?,?,?)',('bazaar',now,digest,raw))
        ref=cur.lastrowid or db.execute('SELECT id FROM source_observations WHERE source=? AND content_hash=?',('bazaar',digest)).fetchone()[0]
        for item in items:
            if isinstance(item,dict): seen[item.get('resource') or item.get('id') or hashlib.sha256(json.dumps(item,sort_keys=True).encode()).hexdigest()]=item
        pages+=1
        if fixture or not items or (total is not None and offset+len(items)>=total): break
    for item in seen.values():
        if not isinstance(item,dict): continue
        accepts=item.get('accepts') or [{}]; acc=accepts[0] if isinstance(accepts,list) and accepts and isinstance(accepts[0],dict) else {}
        url=item.get('resource') or item.get('url') or item.get('endpoint') or ''
        ident=item.get('id') or hashlib.sha256(json.dumps(item,sort_keys=True).encode()).hexdigest()
        network=acc.get('network'); recipient=acc.get('payTo'); asset=acc.get('asset'); price=acc.get('amount')
        meta=hashlib.sha256(json.dumps(item,sort_keys=True).encode()).hexdigest()
        db.execute('INSERT OR IGNORE INTO resources(id,origin,method,path,network,pay_to,first_seen,last_seen) VALUES(?,?,?,?,?,?,?,?)',(ident,item.get('origin'),item.get('method'),item.get('path') or url,network,recipient,now,now))
        db.execute('UPDATE resources SET last_seen=? WHERE id=?',(now,ident))
        db.execute('INSERT OR IGNORE INTO resource_snapshots(resource_id,observed_at,metadata_hash,price,asset,available,rank,raw_ref) VALUES(?,?,?,?,?,?,?,?)',(ident,now,meta,str(price) if price is not None else None,asset,1,None,ref))
    status='COMPLETE_SNAPSHOT' if total is not None and pages*page_size>=total else 'PARTIAL_SNAPSHOT'
    db.execute('INSERT INTO discovery_scans(started_at,finished_at,status,page_count,advertised_total,unique_count,config_json) VALUES(?,?,?,?,?,?,?)',(start,now,status,pages,total,len(seen),json.dumps({'limit':page_size,'max_pages':max_pages})))
    db.execute('INSERT OR REPLACE INTO source_status VALUES(?,?,?,?)',('bazaar','VERIFIED_LIVE',now,f'{status}: {len(seen)} unique of advertised {total}; {pages} pages'))
    db.commit(); return len(seen),status,total,pages

def main():
    p=argparse.ArgumentParser(prog='aie'); sub=p.add_subparsers(dest='cmd',required=True)
    sub.add_parser('sources'); c=sub.add_parser('collect'); c.add_argument('--source',choices=['bazaar','settlements'],required=True); c.add_argument('--fixture'); c.add_argument('--max-pages',type=int,default=5); c.add_argument('--db',default='data/evidence.sqlite'); a=sub.add_parser('analyze'); a.add_argument('--window-days',type=int,default=14); a.add_argument('--db',default='data/evidence.sqlite'); r=sub.add_parser('report'); r.add_argument('--format',choices=['markdown'],default='markdown'); r.add_argument('--db',default='data/evidence.sqlite'); v=sub.add_parser('verify'); v.add_argument('--db',default='data/evidence.sqlite')
    x=p.parse_args()
    if x.cmd=='sources': print(json.dumps(MANIFEST,indent=2)); return
    Path(getattr(x,'db','data/evidence.sqlite')).parent.mkdir(parents=True,exist_ok=True); db=connect(getattr(x,'db','data/evidence.sqlite'))
    if x.cmd=='collect':
        if x.source!='bazaar': print('settlement collector NOT_IMPLEMENTED',file=sys.stderr); sys.exit(2)
        n,s,t,pages=collect(db,x.fixture,x.max_pages); print(f'{s}: {n} unique resources, advertised total {t}, pages {pages}; no purchase attribution inferred.')
    elif x.cmd=='verify': db.execute('PRAGMA integrity_check'); print('SQLite schema initialized; integrity check:',db.execute('PRAGMA integrity_check').fetchone()[0])
    elif x.cmd=='analyze': print(json.dumps({'window_days':x.window_days,'resource_count':db.execute('SELECT count(*) FROM resources').fetchone()[0],'payments_verified':0,'payment_data_status':'UNAVAILABLE','decision':'INSUFFICIENT_DATA'}))
    elif x.cmd=='report':
        n=db.execute('SELECT count(*) FROM resources').fetchone()[0]; print(f'# x402 Newcomer Demand Observatory\n\nDecision: **INSUFFICIENT_DATA**\n\nResources observed: {n}. Settlements verified: 0 (collector unavailable). Resource listings do not prove paid demand. Realized LeftSock income: **$0**.\n\nSources: Bazaar discovery only. Payer independence and resource-level attribution are unverified. See `docs/limitations.md`.')
if __name__=='__main__': main()
