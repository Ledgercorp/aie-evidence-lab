from datetime import datetime,timezone
def render(db):
 scans=db.execute('select id,started_at,status,page_size,advertised_total,unique_count,next_offset from discovery_snapshots order by started_at').fetchall()
 payments=db.execute("select count(*),count(distinct sender) from payments where finality in ('FINAL','CONFIRMED')").fetchone()
 out=['# x402 Newcomer Demand Observatory','',f'Generated {datetime.now(timezone.utc).isoformat()}','', '**Decision: INSUFFICIENT_DATA**','','## Bazaar coverage']
 if not scans:out.append('No persisted scans.')
 for sid,ts,status,size,total,n,offset in scans:
  pages=db.execute('select count(*) from discovery_pages where snapshot_id=?',(sid,)).fetchone()[0]
  out.append(f'- {sid}: {status}, {ts}; {pages} pages of size {size}; {n} unique resources; advertised total {total}; offset {offset}.')
 out+=['','Partial or sampled discovery does not establish launch dates or new businesses. Bazaar quality telemetry is marketplace-reported.','','## Payment evidence',f'- Confirmed/final transfers: {payments[0]}; distinct sender addresses: {payments[1]}.','- No settlement collector is configured. Wallet transfers do not establish resource purchases. Sender addresses are not independent-customer counts.','- No cross-asset amount aggregation is reported.','','## Economic interpretation','- No x402 paid demand is verified by this run. LeftSock realized income: **$0**.','- Missing payment data is unavailable, not a measured zero-demand outcome.','','## System health',f'- SQLite integrity: {db.execute("PRAGMA integrity_check").fetchone()[0]}']
 return '\n'.join(out)+'\n'
