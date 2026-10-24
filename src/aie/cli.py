import argparse,json,sys
from pathlib import Path
from .db import connect
URL='https://api.cdp.coinbase.com/platform/v2/x402/discovery/resources'
def main():
 p=argparse.ArgumentParser(prog='aie');s=p.add_subparsers(dest='cmd',required=True);s.add_parser('sources')
 c=s.add_parser('collect');c.add_argument('--source',choices=['bazaar','settlements'],required=True);c.add_argument('--max-pages',type=int,default=5);c.add_argument('--resume');c.add_argument('--db',default='data/evidence.sqlite')
 a=s.add_parser('analyze');a.add_argument('--window-days',type=int,default=14);a.add_argument('--db',default='data/evidence.sqlite')
 r=s.add_parser('report');r.add_argument('--format',default='markdown');r.add_argument('--db',default='data/evidence.sqlite')
 v=s.add_parser('verify');v.add_argument('--db',default='data/evidence.sqlite');x=p.parse_args()
 if x.cmd=='sources':print(json.dumps({'bazaar':'VERIFIED_LIVE; limit/offset pagination','settlements':'UNAVAILABLE; no verified collector'},indent=2));return
 Path(x.db).parent.mkdir(parents=True,exist_ok=True);d=connect(x.db)
 if x.cmd=='collect':
  if x.source!='bazaar':print('Unavailable; no false zero-activity record.',file=sys.stderr);sys.exit(2)
  from .discovery import scan
  sid,status=scan(d,x.max_pages,100,x.resume);print(sid,status)
 elif x.cmd=='verify':print(d.execute('pragma integrity_check').fetchone()[0])
 elif x.cmd=='report':
  from .reports import render
  print(render(d))
 elif x.cmd=='analyze':
  from .analysis import payer_metrics
  rows=[{'payer':p,'day':day,'amount':amt,'tx_id':tx} for p,day,amt,tx in d.execute("select sender,substr(block_time,1,10),amount_normalized,tx_id from payments where sender is not null and block_time is not null and amount_normalized is not null and finality in ('FINAL','CONFIRMED')")]
  print(json.dumps({'window_days':x.window_days,'snapshots':d.execute('select count(*) from discovery_snapshots').fetchone()[0],'payments':len(rows),'payer_metrics':payer_metrics(rows),'decision':'INSUFFICIENT_DATA'},default=str,indent=2))
if __name__=='__main__':main()
