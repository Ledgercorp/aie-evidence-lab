"""Bounded, resumable Bazaar scans. Each dated snapshot retains payload and resource observations."""
import hashlib,json,time,urllib.error,urllib.parse,urllib.request,uuid
from datetime import datetime,timezone
URL='https://api.cdp.coinbase.com/platform/v2/x402/discovery/resources'
UA='AIE-Evidence-Lab/0.2 (read-only research)'
def now(): return datetime.now(timezone.utc).isoformat()
def fetch_page(offset,limit,timeout=20,retries=3):
 url=URL+'?'+urllib.parse.urlencode({'limit':limit,'offset':offset})
 for i in range(retries+1):
  try:
   req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'application/json'})
   with urllib.request.urlopen(req,timeout=timeout) as r:
    if r.status==402: raise RuntimeError('HTTP 402 is prohibited; no payment retry')
    return json.load(r)
  except urllib.error.HTTPError as e:
   if e.code==402: raise RuntimeError('HTTP 402 is prohibited') from e
   if (e.code!=429 and e.code<500) or i>=retries: raise
   time.sleep(min(2**i,8))
  except (TimeoutError,urllib.error.URLError):
   if i>=retries: raise
   time.sleep(min(2**i,8))
def scan(db,max_pages=5,page_size=100,snapshot_id=None,fetcher=fetch_page):
 if max_pages<1 or page_size<1: raise ValueError('positive bounds required')
 if snapshot_id:
  row=db.execute('select next_offset,page_size,status from discovery_snapshots where id=?',(snapshot_id,)).fetchone()
  if not row: raise ValueError('unknown snapshot')
  offset,size,status=row
  if status=='COMPLETE_SNAPSHOT': return snapshot_id,status
  page_size=size
 else:
  snapshot_id=str(uuid.uuid4()); offset=0
  db.execute('insert into discovery_snapshots(id,started_at,status,page_size,max_pages) values(?,?,?,?,?)',(snapshot_id,now(),'IN_PROGRESS',page_size,max_pages));db.commit()
 initial=db.execute('select count(*) from discovery_pages where snapshot_id=?',(snapshot_id,)).fetchone()[0]
 repeated=False; pages=0
 while pages<max_pages:
  payload=fetcher(offset,page_size)
  if not isinstance(payload,dict) or not isinstance(payload.get('items'),list): raise ValueError('malformed Bazaar page')
  items=payload['items']; meta=payload.get('pagination') or {}; total=meta.get('total')
  if total is not None and (not isinstance(total,int) or total<0): raise ValueError('invalid total')
  raw=json.dumps(payload,sort_keys=True,separators=(',',':')); digest=hashlib.sha256(raw.encode()).hexdigest(); ts=now()
  repeated=db.execute('select 1 from discovery_pages where snapshot_id=? and payload_hash=?',(snapshot_id,digest)).fetchone() is not None
  db.execute('insert or ignore into discovery_pages values(?,?,?,?,?,?,?)',(snapshot_id,offset,ts,digest,len(items),total,raw))
  for item in items:
   if not isinstance(item,dict): continue
   rid=item.get('id') or item.get('resource') or item.get('url') or hashlib.sha256(json.dumps(item,sort_keys=True).encode()).hexdigest()
   encoded=json.dumps(item,sort_keys=True,separators=(',',':'))
   db.execute('insert or ignore into resource_observations values(?,?,?,?,?)',(snapshot_id,str(rid),ts,hashlib.sha256(encoded.encode()).hexdigest(),encoded))
  offset+=len(items); pages+=1
  db.execute('update discovery_snapshots set advertised_total=?,unique_count=(select count(*) from resource_observations where snapshot_id=?),next_offset=? where id=?',(total,snapshot_id,offset,snapshot_id));db.commit()
  if repeated or not items or len(items)<page_size or (total is not None and offset>=total): break
  time.sleep(.5)
 total,unique=db.execute('select advertised_total,unique_count from discovery_snapshots where id=?',(snapshot_id,)).fetchone()
 complete=total is not None and offset>=total and not repeated
 status='COMPLETE_SNAPSHOT' if complete else 'PARTIAL_SNAPSHOT'
 db.execute('update discovery_snapshots set finished_at=?,status=? where id=?',(now(),status,snapshot_id));db.commit()
 return snapshot_id,status
