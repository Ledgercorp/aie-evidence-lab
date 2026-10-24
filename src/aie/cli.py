import argparse,json,sys
from pathlib import Path
from .db import connect
def main():
 p=argparse.ArgumentParser(prog='aie');s=p.add_subparsers(dest='cmd',required=True);s.add_parser('sources')
 c=s.add_parser('collect');c.add_argument('--source',choices=['bazaar','settlements'],required=True);c.add_argument('--max-pages',type=int,default=5);c.add_argument('--resume');c.add_argument('--lookback-blocks',type=int,default=100);c.add_argument('--db',default='data/evidence.sqlite')
 a=s.add_parser('analyze');a.add_argument('--window-days',type=int,default=14);a.add_argument('--db',default='data/evidence.sqlite')
 r=s.add_parser('report');r.add_argument('--format',default='markdown');r.add_argument('--db',default='data/evidence.sqlite')
 v=s.add_parser('verify');v.add_argument('--db',default='data/evidence.sqlite')
 vp=s.add_parser('verify-purchase');vp.add_argument('--evidence',required=True,help='JSON file with signed offer, signed receipt, authorization evidence, and verified ledger transfer');vp.add_argument('--db',default='data/evidence.sqlite')
 vt=s.add_parser('verify-transfer');vt.add_argument('--tx',required=True);vt.add_argument('--event-index',type=int)
 x=p.parse_args()
 if x.cmd=='sources':print(json.dumps({'bazaar':'VERIFIED_LIVE; bounded offset scan','base_usdc':'PublicNode read-only logs','attribution':'payTo match only'},indent=2));return
 if x.cmd=='verify-transfer':
  from .evm import verify_transaction
  print(json.dumps(verify_transaction(x.tx,x.event_index),indent=2,sort_keys=True));return
 Path(x.db).parent.mkdir(parents=True,exist_ok=True);d=connect(x.db)
 if x.cmd=='collect':
  if x.source=='settlements':
   from .evm import collect
   print(json.dumps(collect(d,x.lookback_blocks),indent=2));return
  from .discovery import scan
  sid,status=scan(d,x.max_pages,100,x.resume);print(sid,status)
 elif x.cmd=='verify':print(d.execute('pragma integrity_check').fetchone()[0])
 elif x.cmd=='report':
  from .reports import render
  print(render(d))
 elif x.cmd=='analyze':
  from .analysis import payer_metrics
  rows=[{'payer':p,'day':day,'amount':amt,'tx_id':tx} for p,day,amt,tx in d.execute("select sender,substr(block_time,1,10),amount_normalized,tx_id from payments where finality in ('SAFE','FINAL','CONFIRMED') and sender is not null and amount_normalized is not null")]
  print(json.dumps({'window_days':x.window_days,'payments':len(rows),'payer_metrics':payer_metrics(rows),'decision':'INSUFFICIENT_DATA'},default=str,indent=2))
 elif x.cmd=='verify-purchase':
  from .attribution import verify_purchase,store_verification
  evidence=json.loads(Path(x.evidence).read_text(encoding='utf-8'))
  result=verify_purchase(evidence);store_verification(d,evidence,result)
  print(json.dumps(result,indent=2,sort_keys=True))
if __name__=='__main__':main()
