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

def verify_transaction(tx_hash,event_index=None):
 """Re-fetch and verify one Base USDC transfer at the safe block tag.

 The outer transaction sender is kept separate from ERC-20 Transfer.from: for
 relayed ERC-3009 transfers they need not be the same address.
 """
 if not isinstance(tx_hash,str) or len(tx_hash)!=66 or not tx_hash.startswith('0x'):
  raise ValueError('expected a 32-byte transaction hash')
 if rpc('eth_chainId',[])!=CHAIN:raise RuntimeError('Wrong chain')
 safe=rpc('eth_getBlockByNumber',['safe',False])
 receipt=rpc('eth_getTransactionReceipt',[tx_hash])
 tx=rpc('eth_getTransactionByHash',[tx_hash])
 if not isinstance(receipt,dict) or not isinstance(tx,dict):raise RuntimeError('Transaction or receipt unavailable')
 if receipt.get('transactionHash','').lower()!=tx_hash.lower() or tx.get('hash','').lower()!=tx_hash.lower():raise RuntimeError('Transaction/receipt hash mismatch')
 if receipt.get('status')!='0x1':raise RuntimeError('Transaction did not succeed')
 block_number=int(receipt['blockNumber'],16)
 safe_number=int(safe['number'],16)
 block=rpc('eth_getBlockByNumber',[receipt['blockNumber'],False])
 if not isinstance(block,dict) or block.get('hash','').lower()!=receipt.get('blockHash','').lower():
  raise RuntimeError('Receipt block hash does not match canonical block')
 if block_number>safe_number:raise RuntimeError('Transaction is not at or below the safe block')
 found=[]
 for log in receipt.get('logs',[]):
  topics=log.get('topics',[])
  if log.get('address','').lower()!=USDC or len(topics)<3 or topics[0].lower()!=TRANSFER:continue
  idx=int(log['logIndex'],16)
  if event_index is not None and idx!=int(event_index):continue
  if log.get('removed'):continue
  if len(topics[1])!=66 or len(topics[2])!=66:continue
  found.append({'log_index':idx,'asset':USDC,'from':'0x'+topics[1][-40:].lower(),
   'to':'0x'+topics[2][-40:].lower(),'amount_base':str(int(log['data'],16))})
 if len(found)!=1:raise RuntimeError('Expected exactly one matching canonical Base USDC Transfer log')
 transfer=found[0]
 timestamp=datetime.fromtimestamp(int(block['timestamp'],16),timezone.utc).isoformat()
 return {'status':'LEDGER_CONFIRMED','chain_id':8453,'network':'eip155:8453',
  'transaction_hash':tx_hash.lower(),'block_number':block_number,'block_hash':block['hash'].lower(),
  'block_time':timestamp,'finality':'SAFE','receipt_status':'SUCCESS',
  'outer_transaction_from':tx['from'].lower(),'outer_transaction_to':tx.get('to',None),
  'transfer':transfer,'amount_decimals':'6','amount_normalized':str(Decimal(transfer['amount_base'])/Decimal(10**6)),
  'source_ref':f'{RPC} eth_getTransactionReceipt + eth_getTransactionByHash + safe block {safe_number}',
  'resource_attribution':'NOT_ESTABLISHED','independent_buyer':'NOT_ESTABLISHED'}
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
