"""Standalone evidence snapshots; stdlib only. No network, LLM, or Hermes imports.
Append-only through this API, not a tamper-proof database or a security boundary.
Caller supplies observed_at: historical accuracy depends on trusted ingestion.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import sqlite3
from pathlib import Path


def timestamp(value: str) -> str:
    if not isinstance(value,str):raise ValueError('timestamp must be a timezone-aware string')
    try:parsed=dt.datetime.fromisoformat(value.replace('Z','+00:00'))
    except (TypeError,ValueError) as exc:raise ValueError('invalid timestamp') from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:raise ValueError('timestamp requires timezone')
    return parsed.astimezone(dt.timezone.utc).isoformat(timespec='microseconds').replace('+00:00','Z')


class EvidenceStore:
    def __init__(self,path: str | Path):
        self.db=sqlite3.connect(str(path),timeout=10)
        self.db.row_factory=sqlite3.Row
        version=self.db.execute('PRAGMA user_version').fetchone()[0]
        if version not in (0,1):
            self.db.close();raise ValueError('unsupported evidence schema version')
        with self.db:
            self.db.execute('CREATE TABLE IF NOT EXISTS evidence (evidence_id TEXT PRIMARY KEY, claim_key TEXT NOT NULL, published_at TEXT NOT NULL, observed_at TEXT NOT NULL, payload TEXT NOT NULL)')
            self.db.execute('CREATE INDEX IF NOT EXISTS evidence_claim_time ON evidence(claim_key,published_at,observed_at)')
            self.db.execute('PRAGMA user_version=1')

    def close(self):
        self.db.close()

    def ingest(self,*,evidence_id:str,claim_key:str,source_url:str,passage:str,published_at:str,observed_at:str,value=None)->dict:
        for name,item in [('evidence_id',evidence_id),('claim_key',claim_key),('source_url',source_url),('passage',passage)]:
            if not isinstance(item,str) or not item.strip():raise ValueError(name+' must be nonempty text')
        record={'evidence_id':evidence_id,'claim_key':claim_key,'source_url':source_url,'passage':passage,'published_at':timestamp(published_at),'observed_at':timestamp(observed_at),'value':value,'content_hash':hashlib.sha256(passage.encode('utf-8')).hexdigest()}
        try:payload=json.dumps(record,ensure_ascii=False,sort_keys=True,allow_nan=False,separators=(',',':'))
        except (ValueError,TypeError) as exc:raise ValueError('value must be finite JSON data') from exc
        with self.db:
            old=self.db.execute('SELECT payload FROM evidence WHERE evidence_id=?',(evidence_id,)).fetchone()
            if old is not None:
                if old['payload']!=payload:raise ValueError('immutable evidence_id conflicts with existing snapshot')
                return {'inserted':False,'evidence':json.loads(old['payload'])}
            self.db.execute('INSERT INTO evidence(evidence_id,claim_key,published_at,observed_at,payload) VALUES (?,?,?,?,?)',(evidence_id,claim_key,record['published_at'],record['observed_at'],payload))
        return {'inserted':True,'evidence':json.loads(payload)}

    def history(self,claim_key:str)->list[dict]:
        rows=self.db.execute('SELECT payload FROM evidence WHERE claim_key=? ORDER BY published_at ASC,evidence_id ASC',(claim_key,)).fetchall()
        return [json.loads(r['payload']) for r in rows]

    def query_as_of(self,claim_key:str,cutoff:str,*,mode:str='known_to_system')->dict|None:
        if mode not in ('known_to_system','published_by'):raise ValueError('unsupported temporal mode')
        cutoff=timestamp(cutoff)
        clause=' AND observed_at<=?' if mode=='known_to_system' else ''
        args=(claim_key,cutoff,cutoff) if mode=='known_to_system' else (claim_key,cutoff)
        row=self.db.execute('SELECT payload FROM evidence WHERE claim_key=? AND published_at<=?'+clause+' ORDER BY published_at DESC,evidence_id ASC LIMIT 1',args).fetchone()
        return json.loads(row['payload']) if row else None

    def compare(self,claim_key:str,earlier:str,later:str,*,mode:str='known_to_system')->dict:
        if timestamp(earlier)>timestamp(later):raise ValueError('earlier cutoff exceeds later cutoff')
        before=self.query_as_of(claim_key,earlier,mode=mode)
        after=self.query_as_of(claim_key,later,mode=mode)
        return {'before':before,'after':after,'changed':(before['evidence_id'] if before else None)!=(after['evidence_id'] if after else None)}
