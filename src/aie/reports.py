from datetime import datetime,timezone
import json
def render(db):
 scans=db.execute('select id,started_at,status,page_size,advertised_total,unique_count,next_offset from discovery_snapshots order by started_at').fetchall()
 pay=db.execute("select count(*),count(distinct sender) from payments where finality in ('SAFE','FINAL','CONFIRMED')").fetchone()
 out=['# x402 Newcomer Demand Observatory','',datetime.now(timezone.utc).isoformat(),'','Decision: INSUFFICIENT_DATA','','## Discovery']
 for sid,ts,status,size,total,n,off in scans:
  pages=db.execute('select count(*) from discovery_pages where snapshot_id=?',(sid,)).fetchone()[0]
  out.append(f'Snapshot {sid}: {status}, {pages} pages, {n} unique of changing advertised total {total}, next offset {off}.')
 if not scans:out.append('No snapshots stored.')
 out+=['','Partial rotated windows do not establish launch dates or full-catalog coverage.','',f'## Payment evidence: {pay[0]} safe/final transfers; {pay[1]} sender addresses. Merchant match means payTo address match only. Resource calls and buyer independence are unproven.','', 'No cross-asset amount sum or USD peg assumed. Realized LeftSock income: $0.','',f'SQLite integrity: {db.execute("pragma integrity_check").fetchone()[0]}.']
 return '\n'.join(out)+'\n'
