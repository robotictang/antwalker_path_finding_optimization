"""Frozen-start route comparison: slider experiments never dispatch the robot."""
import math,uuid
import numpy as np
from multiobjective_planner import MultiObjectivePlanner,MODES
from energy_model import normalize_weights,objective_score,required_energy,OBJECTIVE_SCALES
from mission_history import LOCATION_NAMES,LOCATION_POINTS,location_name
from terrain_profile import rough_at
from multi_place_config import DEST_KIOSK_ENTRY,DEST_KIOSK_PAD


class PlanningLab:
    def __init__(self,history=None):self.result=None;self.history=history

    def compare(self,nav,origin='origin',destination=1,weights=(1,1,1),current=None):
        if origin=='current':
            start=np.asarray(current).copy();from_name=location_name(start);yaw=math.pi/2
        else:
            keys=['origin','forest','quarry','marsh','desert','charger']
            if origin not in keys:raise ValueError('Unknown comparison origin')
            i=keys.index(origin);start=LOCATION_POINTS[i].copy();from_name=LOCATION_NAMES[i];yaw=math.pi/2
        target=int(destination)
        if target not in range(4):raise ValueError('Choose one of the four destinations')
        goal=LOCATION_POINTS[target+1];to_name=LOCATION_NAMES[target+1]
        if np.linalg.norm(goal-start)<.5:raise ValueError('Choose different start and destination places')
        weights=normalize_weights(weights);old_mode,old_force=nav.current_mode,nav.force_mode
        try:
            nav.force_mode=None;nav.current_mode='wheels' if origin=='origin' else ('legs' if bool(rough_at(start)) else 'wheels')
            via=[DEST_KIOSK_ENTRY] if origin=='charger' else []
            front,reps=MultiObjectivePlanner(nav).alternatives(start,goal,yaw,weights=weights,via=via)
            nav.current_mode='legs' if bool(rough_at(goal,margin=1.6)) else 'wheels'
            _,returns=MultiObjectivePlanner(nav).alternatives(goal,DEST_KIOSK_PAD,0.,weights=weights,via=[DEST_KIOSK_ENTRY])
            return_cost=returns['energy'].metrics['energy_percent']
        finally:nav.current_mode,nav.force_mode=old_mode,old_force
        front.sort(key=lambda c:c.metrics['distance_m']);rows=[]
        for i,c in enumerate(front):rows.append(dict(c.record(),id=f'R{i+1}',required_battery=required_energy(c.metrics['energy_percent']+return_cost),feasible=required_energy(c.metrics['energy_percent']+return_cost)<=100.+1e-8))
        eligible=[r for r in rows if r['feasible']]
        def best(mode):return min(eligible,key=lambda r:objective_score(r,mode,weights))['id'] if eligible else None
        self.result=dict(id=uuid.uuid4().hex[:10],origin=from_name,destination=to_name,rows=rows,weights=weights.tolist(),scales=OBJECTIVE_SCALES.tolist(),representatives={mode:best(mode) for mode in MODES},map_revision=nav.revision,bounds=[nav.lower,nav.upper],obstacles=nav.boxes.tolist(),error=None if eligible else 'No candidate can cover this task and charger return with a full battery.',note='Fixed start, full battery, automatic terrain. Comparing does not move the robot.')
        if self.history:
            chosen=next((r for r in rows if r['id']==self.result['representatives']['balanced']),None)
            self.history.append('comparison','fixed_start_comparison',from_name,to_name,'compared',details=dict(self.result,mode='balanced',**({k:chosen[k] for k in ('distance_m','estimated_seconds','energy_percent')} if chosen else {})))
        return self.result

    def record_choice(self,comparison_id,weights):
        if not self.result or self.result.get('id')!=comparison_id:return
        weights=normalize_weights(weights);eligible=[r for r in self.result['rows'] if r['feasible']]
        if not eligible:return
        chosen=min(eligible,key=lambda r:objective_score(r,'balanced',weights))
        if self.history:self.history.append('comparison','priorities_previewed',self.result['origin'],self.result['destination'],'preview',details=dict(mode='balanced',weights=weights.tolist(),selected_id=chosen['id'],comparison_id=comparison_id,**{k:chosen[k] for k in ('distance_m','estimated_seconds','energy_percent')}))
