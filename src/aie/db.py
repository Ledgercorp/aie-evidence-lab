import sqlite3
SCHEMA="""
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS source_status(source TEXT PRIMARY KEY,status TEXT NOT NULL,checked_at TEXT,details TEXT);
CREATE TABLE IF NOT EXISTS discovery_snapshots(id TEXT PRIMARY KEY,started_at TEXT NOT NULL,finished_at TEXT,status TEXT NOT NULL,page_size INTEGER NOT NULL,max_pages INTEGER NOT NULL,advertised_total INTEGER,unique_count INTEGER NOT NULL DEFAULT 0,next_offset INTEGER NOT NULL DEFAULT 0,error TEXT);
CREATE TABLE IF NOT EXISTS discovery_pages(snapshot_id TEXT NOT NULL,offset INTEGER NOT NULL,observed_at TEXT NOT NULL,payload_hash TEXT NOT NULL,unique_items INTEGER NOT NULL,advertised_total INTEGER,raw_json TEXT NOT NULL,PRIMARY KEY(snapshot_id,offset));
CREATE TABLE IF NOT EXISTS resource_observations(snapshot_id TEXT NOT NULL,resource_id TEXT NOT NULL,observed_at TEXT NOT NULL,metadata_hash TEXT NOT NULL,raw_json TEXT NOT NULL,PRIMARY KEY(snapshot_id,resource_id));
CREATE TABLE IF NOT EXISTS source_observations(id INTEGER PRIMARY KEY,source TEXT NOT NULL,observed_at TEXT NOT NULL,content_hash TEXT NOT NULL,raw_json TEXT NOT NULL,UNIQUE(source,content_hash));
CREATE TABLE IF NOT EXISTS merchants(id TEXT PRIMARY KEY,identity_confidence TEXT NOT NULL DEFAULT 'UNKNOWN');
CREATE TABLE IF NOT EXISTS resources(id TEXT PRIMARY KEY,merchant_id TEXT,origin TEXT,method TEXT,path TEXT,network TEXT,pay_to TEXT,first_seen TEXT NOT NULL,last_seen TEXT NOT NULL,created_at_known INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS resource_snapshots(id INTEGER PRIMARY KEY,resource_id TEXT NOT NULL,observed_at TEXT NOT NULL,metadata_hash TEXT NOT NULL,price TEXT,asset TEXT,available INTEGER,rank INTEGER,raw_ref INTEGER,UNIQUE(resource_id,observed_at,metadata_hash));
CREATE TABLE IF NOT EXISTS payments(chain TEXT NOT NULL,tx_id TEXT NOT NULL,event_index TEXT NOT NULL,block_number INTEGER,block_time TEXT,sender TEXT,recipient TEXT,asset TEXT,amount_base TEXT,decimals INTEGER,amount_normalized TEXT,finality TEXT NOT NULL,usd_estimate TEXT,usd_basis TEXT,PRIMARY KEY(chain,tx_id,event_index));
CREATE TABLE IF NOT EXISTS payment_attributions(chain TEXT NOT NULL,tx_id TEXT NOT NULL,event_index TEXT NOT NULL,merchant_id TEXT,resource_id TEXT,level TEXT NOT NULL,confidence TEXT NOT NULL,evidence_ref TEXT);
CREATE TABLE IF NOT EXISTS merchant_cohorts(merchant_id TEXT PRIMARY KEY,first_seen TEXT NOT NULL,followup_days INTEGER,censored INTEGER NOT NULL DEFAULT 1,bootstrap_known INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS payer_activity(chain TEXT NOT NULL,tx_id TEXT NOT NULL,event_index TEXT NOT NULL,payer TEXT NOT NULL,day TEXT NOT NULL,PRIMARY KEY(chain,tx_id,event_index));
CREATE TABLE IF NOT EXISTS evidence(id INTEGER PRIMARY KEY,kind TEXT NOT NULL,classification TEXT NOT NULL,source_ref TEXT NOT NULL,provenance TEXT NOT NULL,confidence TEXT);
CREATE TABLE IF NOT EXISTS analysis_runs(id INTEGER PRIMARY KEY,ran_at TEXT NOT NULL,config_json TEXT NOT NULL,code_version TEXT,snapshot_hash TEXT,output_hash TEXT);
"""
def connect(path):
 db=sqlite3.connect(path);db.executescript(SCHEMA);return db
