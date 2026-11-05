"""A staged, physical roadwork obstruction demonstrates on-route detection/replanning.

The global map initially predates the roadwork; the simulated proximity sensor
updates it within 8 m. This is an explicit demonstration, not a LiDAR pipeline.
"""
import numpy as np
import mujoco
from safe_navigation import SafeNavigator
from multi_place_config import DEST_BASE,DEST_KIOSK_ENTRY,DEST_KIOSK_PAD,MISSION_TARGETS,CHARGING_STATIONS


class RoadworkDemo:
    def __init__(self,m,d,enabled=True):
        self.m=m;self.d=d;self.enabled=enabled;self.placed=False;self.detected=False
        self.position=None;self.events=[];self.placed_time=None;self.cleared=False
        self.mocap=int(m.body_mocapid[m.body('roadwork_obstacle').id])

    def stage(self,mission,nav):
        if not self.enabled or self.placed or mission.stage!='preview' or mission.divert:return
        points=mission.full_route
        distance=0.
        candidates=[]
        for a,b in zip(points,points[1:]):
            length=float(np.linalg.norm(b-a))
            for t in np.arange(.5,length,.75):
                along=distance+t
                if 9.<along<19. and np.linalg.norm(a+(b-a)*t/length-mission.position)>8.5:
                    candidates.append(a+(b-a)*t/length)
            distance+=length
        # Verify that a safe replacement path exists before staging roadwork.
        for point in candidates:
            # Keep the charging approach open; a demonstration obstacle must not
            # disconnect a site from its only charging station.
            if abs(point[0])<3.5 and -14.<point[1]<5.:continue
            self.d.mocap_pos[self.mocap]=[*point,0.]
            mujoco.mj_forward(self.m,self.d)
            fresh=SafeNavigator(self.m,self.d);fresh.current_mode=nav.current_mode;fresh.force_mode=nav.force_mode
            targets=[DEST_BASE,DEST_KIOSK_ENTRY,DEST_KIOSK_PAD]+[t['pos'] for t in MISSION_TARGETS]+[s['pos'] for s in CHARGING_STATIONS]
            if not all(fresh.clear(p) for p in targets):continue
            cells=[fresh.nearest_free(p) for p in targets]
            try:
                from scipy.ndimage import label
                components,_=label(~fresh.blocked)
                if not all(components[c]==components[cells[0]] and components[c]>0 for c in cells):continue
            except ImportError:
                try:
                    for endpoint in targets[1:]:fresh.plan(targets[0],endpoint,mode='shortest')
                except RuntimeError:continue
            try:
                fresh.plan(mission.position,mission.route[-1],mode=mission.mode,yaw=mission.yaw,weights=mission.weights)
            except RuntimeError:continue
            self.placed=True;self.position=point.copy();self.placed_time=float(self.d.time)
            self.events.append(dict(event='roadwork_staged',time=float(self.d.time),position=point.tolist()))
            print('Roadwork now occupies the planned lane; local detection updates the map within 8 m.',flush=True)
            return
        self.d.mocap_pos[self.mocap]=[100.,100.,0.]
        mujoco.mj_forward(self.m,self.d)
        self.placed=True
        self.events.append(dict(event='roadwork_not_staged',reason='No verified safe detour at candidate positions'))

    def sense(self,mission,nav):
        # External clearance of temporary demo roadwork is a map change, not free energy.
        if self.placed_time is not None and not self.cleared and float(self.d.time)-self.placed_time>=90.:
            self.cleared=True;self.position=None
            self.d.mocap_pos[self.mocap]=[100.,100.,0.]
            mujoco.mj_forward(self.m,self.d)
            fresh=SafeNavigator(self.m,self.d);fresh.current_mode=nav.current_mode;fresh.force_mode=nav.force_mode
            mission.navigator=fresh
            if mission.stage in ('moving','preview','blocked'):
                mission.pending_target='charger' if mission.divert else mission.target
                if mission.pending_target is not None:mission.stage='stopping';mission.error=None
            mission.notice='TEMPORARY ROADWORK CLEARED - map and energy budget updated'
            mission.notice_until=mission.elapsed+10.
            mission.events.append(dict(event='roadwork_cleared',time=mission.elapsed))
            self.events.append(dict(event='roadwork_cleared',time=float(self.d.time)))
            return fresh
        if self.position is None or self.detected or np.linalg.norm(mission.position-self.position)>8.:return nav
        self.detected=True
        fresh=SafeNavigator(self.m,self.d);fresh.current_mode=nav.current_mode;fresh.force_mode=nav.force_mode
        mission.navigator=fresh;mission.avoid_obstacle()
        self.events.append(dict(event='roadwork_detected',time=float(self.d.time),distance_m=float(np.linalg.norm(mission.position-self.position))))
        return fresh
