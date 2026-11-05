"""Append-only SQLite trip/plan/event history, retained across refresh and resets."""
from pathlib import Path
from datetime import datetime,timezone
import sqlite3,json,uuid,csv,io,hashlib,math
from contextlib import contextmanager
import numpy as np
from multi_place_config import DEST_BASE,DEST_KIOSK_PAD,MISSION_TARGETS,PLACE_LABELS,CHARGING_STATIONS

LOCATION_NAMES=['Origin depot']+PLACE_LABELS+[s['name']+' charging station' for s in CHARGING_STATIONS]
LOCATION_POINTS=[np.asarray(DEST_BASE)]+[np.asarray(t['pos']) for t in MISSION_TARGETS]+[np.asarray(s['pos']) for s in CHARGING_STATIONS]


def location_name(point):
    p=np.asarray(point,dtype=float);dist=[float(np.linalg.norm(p-q)) for q in LOCATION_POINTS]
    i=int(np.argmin(dist))
    return LOCATION_NAMES[i] if dist[i]<2. else f'En route ({p[0]:.1f}, {p[1]:.1f})'


def json_safe(value):
    if isinstance(value,dict):return {str(k):json_safe(v) for k,v in value.items()}
    if isinstance(value,(list,tuple,np.ndarray)):return [json_safe(v) for v in value]
    if isinstance(value,np.generic):return json_safe(value.item())
    if isinstance(value,float) and not math.isfinite(value):return None
    return value


def recovered_destination(event):
    if event.get('event') in ('low_battery_diversion','energy_charging_diversion','charging_requested','charge_complete') or event.get('decision')=='charging_route':return 'Charging station'
    if event.get('to_name'):return event['to_name']
    return 'Previous destination unavailable'


class HistoryStore:
    def __init__(self,path,start_session=True):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True);self.session=uuid.uuid4().hex[:12]
        with self.connect() as c:
            c.execute('PRAGMA journal_mode=WAL')
            c.execute('CREATE TABLE IF NOT EXISTS records (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL, session TEXT NOT NULL, sim_time REAL, category TEXT, kind TEXT, origin TEXT, destination TEXT, status TEXT, details TEXT NOT NULL)')
            c.execute('CREATE TABLE IF NOT EXISTS imported (fingerprint TEXT PRIMARY KEY)')
        if start_session:self.append('session','simulation_started',status='started',details={'message':'History survives browser refresh, robot reset and simulator restart.'})

    @contextmanager
    def connect(self):
        c=sqlite3.connect(str(self.path),timeout=10);c.row_factory=sqlite3.Row
        try:
            yield c
            c.commit()
        finally:c.close()

    def append(self,category,kind,origin='',destination='',status='',sim_time=0.,details=None):
        with self.connect() as c:
            c.execute('INSERT INTO records(timestamp,session,sim_time,category,kind,origin,destination,status,details) VALUES(?,?,?,?,?,?,?,?,?)',(datetime.now(timezone.utc).isoformat(timespec='seconds'),self.session,float(sim_time),category,kind,origin,destination,status,json.dumps(json_safe(details or {}),allow_nan=False)))

    def page(self,before=None,limit=50,category='all',after=None):
        limit=max(1,min(200,int(limit)));clauses=[];args=[]
        if after is not None:clauses.append('id > ?');args.append(int(after))
        if before:clauses.append('id < ?');args.append(int(before))
        if category!='all':clauses.append('category = ?');args.append(category)
        where=' WHERE '+' AND '.join(clauses) if clauses else ''
        with self.connect() as c:
            rows=c.execute('SELECT * FROM records'+where+(' ORDER BY id ASC LIMIT ?' if after is not None else ' ORDER BY id DESC LIMIT ?'),args+[limit]).fetchall()
            total=c.execute('SELECT COUNT(*) FROM records').fetchone()[0]
        data=[dict(r) for r in rows]
        for row in data:
            details=json.loads(row['details'])
            row['details']={k:v for k,v in details.items() if k not in ('points','pareto_front','obstacles','rows')}
            if 'rows' in details:row['details']['candidate_count']=len(details['rows'])
        return dict(records=data,total=total,next_before=data[-1]['id'] if data else None,next_after=data[-1]['id'] if data else after,has_more=len(data)==limit)

    def csv(self):
        with self.connect() as c:rows=c.execute('SELECT * FROM records ORDER BY id').fetchall()
        stream=io.StringIO();writer=csv.writer(stream);writer.writerow(['ID','Timestamp','Session','Simulation seconds','Type','Event','From','To','Status','Distance m','Estimate s','Energy %','Details JSON'])
        for row in rows:
            d=json.loads(row['details']);writer.writerow([row['id'],row['timestamp'],row['session'],row['sim_time'],row['category'],row['kind'],row['origin'],row['destination'],row['status'],d.get('distance_m',''),d.get('estimated_seconds',''),d.get('energy_percent',''),row['details']])
        return stream.getvalue().encode()

    def recover(self,snapshot):
        snapshot=Path(snapshot)
        if not snapshot.exists():return
        raw=snapshot.read_bytes();fingerprint=hashlib.sha256(raw).hexdigest()
        with self.connect() as c:
            if c.execute('SELECT 1 FROM imported WHERE fingerprint=?',(fingerprint,)).fetchone():return
        state=json.loads(raw)
        for event in state.get('events',[]):
            event_key='live-event:'+hashlib.sha256(json.dumps(event,sort_keys=True).encode()).hexdigest()
            with self.connect() as c:
                if c.execute('SELECT 1 FROM imported WHERE fingerprint=?',(event_key,)).fetchone():continue
            self.append('recovered',event.get('event','previous_event'),origin='Previous session (origin unavailable)',destination=recovered_destination(event),status='recovered',sim_time=event.get('time',0.),details=event)
            with self.connect() as c:c.execute('INSERT OR IGNORE INTO imported(fingerprint) VALUES(?)',(event_key,))
        with self.connect() as c:c.execute('INSERT OR IGNORE INTO imported(fingerprint) VALUES(?)',(fingerprint,))


class HistoryRecorder:
    def __init__(self,store):self.store=store;self.mission=None;self.counts=[0,0,0]

    def observe(self,mission):
        if mission is not self.mission:self.mission=mission;self.counts=[0,0,0]
        for index,(items,category) in enumerate([(mission.events,'event'),(mission.plans,'plan'),(mission.arrivals,'trip')]):
            for record in items[self.counts[index]:]:
                origin=record.get('from_name',record.get('origin',getattr(mission,'journey_origin','')))
                destination=record.get('to_name',record.get('destination_name',''))
                if not destination:
                    destination=mission.destination_name if mission.divert or mission.charging else (LOCATION_NAMES[mission.target+1] if mission.target is not None else '')
                kind=record.get('event','route_planned' if category=='plan' else 'arrived')
                if kind in ('destination_requested','destination_cancelled'):category_for_record='trip'
                else:category_for_record=category
                self.store.append(category_for_record,kind,origin,destination,record.get('status',mission.stage),record.get('time',mission.elapsed),record)
            self.counts[index]=len(items)
