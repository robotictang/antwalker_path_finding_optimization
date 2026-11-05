"""Shared geometry-checked follower for the V6 mission pipeline.

This changes tracking, not obstacle geometry or the safety guard. Prescribed
body assistance is still present and explicitly reported by execution.py.
"""
import math
import numpy as np

PARAMETERS=dict(arrival_radius=.10,connector_margin=.04,align_enter=.25,
                align_exit=.06,braking_offset=.015,recovery_after_s=1.5,
                stop_after_s=6.,maximum_recoveries=2)

class SafeFollower:
    def __init__(self,nav):
        self.nav=nav;self.aligning=False;self.anchor=None;self.blocked_seconds=0.
        self.recoveries=0;self.events=[];self.advance_checks=0
    def may_advance(self,xy,points,index):
        if np.linalg.norm(points[index]-xy)>=PARAMETERS['arrival_radius']:return False
        if index+1==len(points):return True
        self.advance_checks+=1
        return self.nav.segment_clear(xy,points[index+1],margin=PARAMETERS['connector_margin'])
    def target(self,xy,points,index):
        if self.anchor is not None and np.linalg.norm(self.anchor-xy)<PARAMETERS['arrival_radius']:
            self.anchor=None;self.blocked_seconds=0.;self.aligning=True
        return points[index] if self.anchor is None else self.anchor
    def translation_allowed(self,heading_error):
        if abs(heading_error)>PARAMETERS['align_enter']:self.aligning=True
        if abs(heading_error)<PARAMETERS['align_exit']:self.aligning=False
        return not self.aligning
    def observe_guard(self,xy,points,index,blocked,seconds,clock):
        self.blocked_seconds=self.blocked_seconds+seconds if blocked else 0.
        if self.blocked_seconds>=PARAMETERS['stop_after_s']:return 'tracking_guard'
        if self.blocked_seconds<PARAMETERS['recovery_after_s'] or self.anchor is not None:return None
        if self.recoveries>=PARAMETERS['maximum_recoveries']:return None
        previous=points[max(0,index-1)]
        if np.linalg.norm(previous-xy)>PARAMETERS['arrival_radius'] and self.nav.segment_clear(xy,previous,margin=PARAMETERS['connector_margin']):
            self.anchor=previous.copy();self.recoveries+=1;self.aligning=True;self.blocked_seconds=0.
            self.events.append(dict(time_s=float(clock),event='safe_backtrack',waypoint=index,anchor=previous.tolist()))
        return None
