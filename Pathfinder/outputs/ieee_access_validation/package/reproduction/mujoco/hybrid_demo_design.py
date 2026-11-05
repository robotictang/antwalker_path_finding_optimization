"""Restored demonstration geometry with better-proportioned wheels and suspension detail."""
import math
import xml.etree.ElementTree as ET
import numpy as np
from strict_asset import SOURCE_MESH_DIR, ACTUATOR_REPLACEMENT, validate_sources

WHEEL_RADIUS=.15
WHEEL_TRACK=1.12
DRIVE_HEIGHT=.31
WALK_HEIGHT=.50


def apply_hybrid_demo(root):
    validate_sources()
    for mesh in root.findall('asset/mesh'):
        if mesh.get('name','').startswith('mesh_'):
            file=ACTUATOR_REPLACEMENT if mesh.get('name')=='mesh_rs04_actuator' else SOURCE_MESH_DIR/mesh.get('file').split('/')[-1]
            mesh.set('file',str(file))
    robot=root.find(".//body[@name='robot']")
    robot.set('pos',f'0 -20 {DRIVE_HEIGHT}')
    # Explicit demo inertias avoid assigning giant masses from collision-envelope volumes.
    ET.SubElement(robot,'inertial',mass='46',pos='0 0 .18',diaginertia='4.5 4.8 7.5')
    for part,mass,inertia,position in [('coxa',2.02,'0.009 0.007 0.012','0 .078 0'),('femur',3.49,'0.018 0.082 0.085','0 .35 0'),('tibia',4.71,'0.215 0.218 0.015','0 .38 0')]:
        for leg in ('LF','LM','LR','RF','RM','RR'):
            body=robot.find(f".//body[@name='{part}_{leg}']")
            ET.SubElement(body,'inertial',mass=str(mass),pos=position,diaginertia=inertia)
    default=root.find("default/default[@class='wheel_geom']/geom")
    default.set('size',f'{WHEEL_RADIUS} .06')
    default.set('friction','1.8 .02 .001')
    for name,sx,sy in [('FL',1,1),('FR',1,-1),('RL',-1,1),('RR',-1,-1)]:
        body=robot.find(f"body[@name='wheel_{name}']")
        body.set('pos',f'{sx*.50} {sy*.56} -.16')
        ET.SubElement(body,'inertial',mass='1.5',pos='0 0 0',diaginertia='.01024 .016875 .01024')
        for g in list(body.findall('geom')):
            if g.get('class')=='wheel_geom':
                g.set('name','tire_'+name)
                continue
            if g.get('type')=='box':
                body.remove(g);continue
            if g.get('pos'):
                pos=np.fromstring(g.get('pos'),sep=' ')*[WHEEL_RADIUS/.09,.06/.035,WHEEL_RADIUS/.09]
                g.set('pos',' '.join(map(str,pos)))
            if g.get('size'):
                size=np.fromstring(g.get('size'),sep=' ')*[WHEEL_RADIUS/.09,.06/.035]
                g.set('size',' '.join(map(str,size)))
        for k in range(20):
            theta=2*math.pi*k/20
            ET.SubElement(body,'geom',name=f'tread_{name}_{k}',type='box',size='.012 .062 .004',pos=f'{.146*math.cos(theta)} 0 {.146*math.sin(theta)}',euler=f'0 {math.pi/2-theta} 0',material='wheel_mat',contype='0',conaffinity='0',density='.01')
        # Display suspension linkage follows the enlarged axle stance; no unsupported spring physics claimed.
        for tag,radius,z0,z1,material in [('arm',.022,-.015,-.16,'carapace_titanium_trim'),('damper',.016,.08,-.10,'carapace_accent_orange')]:
            ET.SubElement(robot,'geom',name=f'wheel_{tag}_{name}',type='capsule',size=str(radius),fromto=f'{sx*.40} {sy*.38} {z0} {sx*.50} {sy*.56} {z1}',material=material,contype='0',conaffinity='0',density='.01')
    # Align each femur hook tip with its side-pocket socket in the latched pose.
    for leg in ('LF','LM','LR','RF','RM','RR'):
        robot.find(f".//geom[@name='hook_mount_{leg}']").set('pos','0 .615 .042')
        robot.find(f".//geom[@name='hook_shank_{leg}']").set('fromto','0 .615 .042 0 .639 -.025')
        robot.find(f".//geom[@name='hook_claw_{leg}']").set('fromto','0 .639 -.025 0 .639 -.044')
        robot.find(f".//geom[@name='hook_tip_{leg}']").set('pos','0 .639 -.048')
    for i in range(1,6):
        robot.find(f"geom[@name='bat_led_{i}']").set('size','.014 .004 .009')
    # Keep the physical scanner hardware but remove the giant decorative beam fan.
    for body in robot.iter('body'):
        for geom in list(body.findall('geom')):
            if geom.get('name','').startswith(('lidar_beam','lidar_outline','lidar_wave_ring')):
                body.remove(geom)
    for actuator in root.findall('actuator/position'):
        if actuator.get('joint','').startswith(('coxa_joint_','femur_joint_','tibia_joint_')):
            actuator.set('forcerange','-60 60')
    for actuator in root.findall('actuator/velocity'):
        if 'wheel' in actuator.get('joint',''):
            actuator.set('forcerange','-30 30')
    root.set('model','hybrid_hexapod_pathfinding_demo')
