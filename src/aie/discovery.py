"""Resumable rotating Bazaar offset scan; partial windows never imply completeness."""
import hashlib,json,time,urllib.error,urllib.parse,urllib.request,uuid
from datetime import datetime,timezone
URL='https://api.cdp.coinbase.com/platform/v2/x402/discovery/resources';UA='AIE Evidence Lab read-only'
def now():return datetime.now(timezone.utc).isoformat()
def fetch_page(offset,limit,timeout=20,retries=3):
 u=URL+'?'+urllib.parse.urlencode({'limit':limit,'offset':offset})
 for i in range(retries+1):
  try:
   q=urllib.request.Request(u,headers={'User-Agent':UA,'Accept':'application/json'})
   with urllib.request.urlopen(q,timeout=timeout) as r:return json.load(r)
  except urllib.error.HTTPError as e:
   if e.code==402:raise RuntimeError('402 payment prohibited')
   if (e.code!=429 and e.code<500) or i==retries:raise
   time.sleep(min(2**i,8))
  except (TimeoutError,urllib.error.URLError):
   if i==retries:raise
   time.sleep(min(2**i,8))
def scan(db,max_pages=5,page_size=100,snapshot_id=None,fetcher=fetch_page):
 if not 1<=max_pages<=10 or not 1<=page_size<=100:raise ValueError('collection bounds exceeded')
 if snapshot_id:
  row=db.execute('select next_offset,page_size,status from discovery_snapshots where id=?',(snapshot_id,)).fetchone()
  if not row:raise ValueError('unknown snapshot')
  offset,size,status=row
  if status=='COMPLETE_SNAPSHOT':return snapshot_id,status
  page_size=size;start=db.execute('select min(offset) from discovery_pages where snapshot_id=?',(snapshot_id,)).fetchone()[0] or 0
 else:
  snapshot_id=str(uuid.uuid4());cur=db.execute("select next_offset,advertised_total from discovery_cursor where source='bazaar'").fetchone()
  if cur:offset=cur[0] if cur[1] else 0
  else:
   prior=db.execute('select next_offset,advertised_total from discovery_snapshots order by started_at desc limit 1').fetchone();offset=prior[0] if prior and prior[1] else 0
  start=offset;db.execute('insert into discovery_snapshots(id,started_at,status,page_size,max_pages) values(?,?,?,?,?)',(snapshot_id,now(),'IN_PROGRESS',page_size,max_pages));db.commit()
 pages=0;repeat=False;totals=set()
 while pages<max_pages:
  payload=fetcher(offset,page_size)
  if not isinstance(payload,dict) or not isinstance(payload.get('items'),list):raise ValueError('invalid page')
  items=payload['items'];total=(payload.get('pagination') or {}).get('total')
  if not isinstance(total,int) or total<0:raise ValueError('invalid pagination.total')
  totals.add(total);raw=json.dumps(payload,sort_keys=True,separators=(',',':'));digest=hashlib.sha256(raw.encode()).hexdigest();ts=now()
  repeat=db.execute('select 1 from discovery_pages where snapshot_id=? and payload_hash=?',(snapshot_id,digest)).fetchone() is not None
  db.execute('insert or ignore into discovery_pages values(?,?,?,?,?,?,?)',(snapshot_id,offset,ts,digest,len(items),total,raw))
  for item in items:
   if isinstance(item,dict):
    rid=item.get('id') or item.get('resource') or item.get('url') or hashlib.sha256(json.dumps(item,sort_keys=True).encode()).hexdigest();enc=json.dumps(item,sort_keys=True,separators=(',',':'))
    db.execute('insert or ignore into resource_observations values(?,?,?,?,?)',(snapshot_id,str(rid),ts,hashlib.sha256(enc.encode()).hexdigest(),enc))
  offset+=len(items);pages+=1;unique=db.execute('select count(*) from resource_observations where snapshot_id=?',(snapshot_id,)).fetchone()[0]
  db.execute('update discovery_snapshots set advertised_total=?,unique_count=?,next_offset=? where id=?',(total,unique,offset,snapshot_id))
  db.execute("insert into discovery_cursor values('bazaar',?,?,?,'rotating_sequential_offset') on conflict(source) do update set next_offset=excluded.next_offset,advertised_total=excluded.advertised_total,updated_at=excluded.updated_at,method=excluded.method",(0 if offset>=total else offset,total,now()));db.commit()
  if repeat or not items or len(items)<page_size or offset>=total:break
  time.sleep(.5)
 total,unique=db.execute('select advertised_total,unique_count from discovery_snapshots where id=?',(snapshot_id,)).fetchone()
 status='COMPLETE_SNAPSHOT' if start==0 and offset>=total and unique>=total and len(totals)==1 and not repeat else 'PARTIAL_SNAPSHOT'
 db.execute('update discovery_snapshots set finished_at=?,status=?,error=? where id=?',(now(),status,'CATALOG_TOTAL_CHANGED' if len(totals)>1 else None,snapshot_id));db.commit()
 return snapshot_id,status
