"""Read-only Base USDC Transfer logs. Address match is not resource attribution."""
import json,urllib.request
from datetime import datetime,timezone
from decimal import Decimal
RPC='https://base-rpc.publicnode.com';CHAIN='0x2105';USDC='0x833589fcd6edb6e08f4c7c32d4f71b54bda02913';TRANSFER='0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
def rpc(method,params):
 data=json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':params}).encode();q=urllib.request.Request(RPC,data=data,headers={'Content-Type':'application/json','User-Agent':'AIE-Evidence-Lab read-only'})
 with urllib.request.urlopen(q,timeout=15) as r:v=json.load(r)
 if v.get('error'):raise RuntimeError(str(v['error']))
 return v.get('result')
def collect(db,lookback=100,limit=25):
 if not 1<=lookback<=500 or not 1<=limit<=25:raise ValueError('RPC bounds exceeded')
 if rpc('eth_chainId',[])!=CHAIN:raise RuntimeError('Wrong chain')
 safe=rpc('eth_getBlockByNumber',['safe',False]); end=int(safe['number'],16); start=max(0,end-lookback+1)
 addrs=set()
 for (raw,) in db.execute('select raw_json from resource_observations'):
  for a in json.loads(raw).get('accepts',[]):
   p=a.get('payTo','').lower() if isinstance(a,dict) else ''
   if len(p)==42 and p.startswith('0x'):addrs.add(p)
 addrs=sorted(addrs)[:limit]
 if not addrs:return {'status':'NO_ADDRESSES_TO_QUERY','to_block':end,'records_ingested':0}
 topics=[TRANSFER,None,['0x'+'0'*24+a[2:] for a in addrs]]
 logs=rpc('eth_getLogs',[{'fromBlock':hex(start),'toBlock':hex(end),'address':USDC,'topics':topics}])
 if not isinstance(logs,list):raise RuntimeError('Invalid logs response')
 blocks={};count=0
 for x in logs:
  ts=x.get('topics',[])
  if x.get('removed') or x.get('address','').lower()!=USDC or len(ts)<3 or ts[0].lower()!=TRANSFER:continue
  tx=x['transactionHash'].lower();idx=str(int(x['logIndex'],16));bn=int(x['blockNumber'],16);sender='0x'+ts[1][-40:].lower();recipient='0x'+ts[2][-40:].lower();base=str(int(x['data'],16));amount=str(Decimal(base)/Decimal(10**6))
  if bn not in blocks:
   b=rpc('eth_getBlockByNumber',[hex(bn),False]);blocks[bn]=datetime.fromtimestamp(int(b['timestamp'],16),timezone.utc).isoformat()
  db.execute("insert or ignore into payments values(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(CHAIN,tx,idx,bn,blocks[bn],sender,recipient,USDC,base,6,amount,'SAFE',None,'nominal USDC; USD peg not assumed'))
  db.execute('insert or ignore into payment_attributions(chain,tx_id,event_index,merchant_id,resource_id,level,confidence,evidence_ref) values(?,?,?,?,?,?,?,?)',(CHAIN,tx,idx,recipient,'','MERCHANT_ASSOCIATED','ADDRESS_MATCH_ONLY',f'{RPC} eth_getLogs {start}:{end} {USDC}'))
  db.execute('insert into evidence(kind,classification,source_ref,provenance,confidence) values(?,?,?,?,?)',('EVM_LOG','MERCHANT_ASSOCIATED',f'{CHAIN}:{tx}:{idx}',json.dumps({'rpc':RPC,'contract':USDC,'safe_block':safe['number'],'block_hash':x.get('blockHash')}),'SAFE_RPC_LOG'));count+=1
 db.execute('insert or replace into source_status values(?,?,?,?)',('base_usdc','VERIFIED_LIVE',datetime.now(timezone.utc).isoformat(),f'safe blocks {start}-{end}; {count} logs; {len(addrs)} payTo addresses queried'));db.commit()
 return {'chain_id':CHAIN,'from_block':start,'to_block':end,'records_ingested':count,'addresses':len(addrs),'resource_attribution':'NOT_ESTABLISHED','independent_buyers':'NOT_ESTABLISHED'}
