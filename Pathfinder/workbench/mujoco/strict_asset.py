"""Render only supplied mesh visuals, with assembly transforms from the source URDF."""
from pathlib import Path
import hashlib
import json
import math
import re
import struct
import xml.etree.ElementTree as ET

SOURCE_ROOT = Path(__file__).resolve().parents[1]
SOURCE_MESH_DIR = SOURCE_ROOT / 'meshes'
ACTUATOR_REPLACEMENT = Path(__file__).resolve().parent / 'derived_meshes/rs04_actuator_mujoco.stl'
REQUIRED_MESHES = ('base_link.stl','coxa_link.stl','femur_link.stl','tibia_link.stl','rs04_actuator.stl','top_cover.stl')


class MissingAssetError(RuntimeError):
    pass


def validate_sources(require_hybrid=False):
    errors=[]
    for name in REQUIRED_MESHES:
        path=SOURCE_MESH_DIR/name
        if not path.is_file():
            errors.append(f'Missing supplied mesh: {path}')
            continue
        blob=path.read_bytes()
        if len(blob)<84 or len(blob)!=84+50*struct.unpack_from('<I',blob,80)[0]:
            errors.append(f'Invalid binary STL: {path}')
    if not (SOURCE_ROOT/'hexapod.urdf').is_file():
        errors.append(f'Missing assembly definition: {SOURCE_ROOT / "hexapod.urdf"}')
    if errors:
        raise MissingAssetError('\n'.join(errors))
    urdf=ET.fromstring(re.sub(r'<!--.*?-->', '', (SOURCE_ROOT/'hexapod.urdf').read_text(), flags=re.S))
    for mesh in urdf.findall('.//visual/geometry/mesh'):
        path=SOURCE_ROOT/mesh.get('filename')
        if not path.is_file():
            errors.append(f'Missing URDF visual mesh: {path}')
    if require_hybrid:
        if not any('wheel' in j.get('name','').lower() for j in urdf.findall('joint')):
            errors.append('Missing wheel assembly: supplied meshes/URDF contain no wheel asset or wheel joint definitions. Hybrid wheel/leg mission cannot start.')
        unsupported=[link.get('name') for link in urdf.findall('link') if any(v.find('geometry/mesh') is None for v in link.findall('visual'))]
        if unsupported:
            errors.append('Missing mesh visuals for '+', '.join(unsupported)+': the URDF specifies primitive foot spheres; replacement geometry is prohibited.')
    if not ACTUATOR_REPLACEMENT.is_file():
        errors.append(f'Missing authorized actuator replacement: {ACTUATOR_REPLACEMENT}')
    else:
        blob=ACTUATOR_REPLACEMENT.read_bytes()
        if len(blob)<84 or len(blob)!=84+50*struct.unpack_from('<I',blob,80)[0] or struct.unpack_from('<I',blob,80)[0]>200000:
            errors.append(f'Invalid or unsupported actuator replacement: {ACTUATOR_REPLACEMENT}')
    provenance=ACTUATOR_REPLACEMENT.parent/'actuator_provenance.json'
    if not provenance.is_file():
        errors.append(f'Missing actuator provenance: {provenance}')
    elif ACTUATOR_REPLACEMENT.is_file():
        record=json.loads(provenance.read_text())
        if record['source_sha256']!=hashlib.sha256((SOURCE_MESH_DIR/'rs04_actuator.stl').read_bytes()).hexdigest():
            errors.append('Actuator source changed; regenerate the authorized replacement.')
        if record['replacement_sha256']!=hashlib.sha256(ACTUATOR_REPLACEMENT.read_bytes()).hexdigest():
            errors.append('Actuator replacement hash does not match its provenance record.')
    if errors:
        raise MissingAssetError('\n'.join(errors))
    return urdf


def origin_attributes(element):
    if element is None:
        return {}
    r,p,y=map(float,element.get('rpy','0 0 0').split())
    cr,cp,cy=math.cos(r/2),math.cos(p/2),math.cos(y/2)
    sr,sp,sy=math.sin(r/2),math.sin(p/2),math.sin(y/2)
    quat=(cr*cp*cy+sr*sp*sy,sr*cp*cy-cr*sp*sy,cr*sp*cy+sr*cp*sy,cr*cp*sy-sr*sp*cy)
    return {'pos':element.get('xyz','0 0 0'),'quat':' '.join(map(str,quat))}


def build_robot_xml():
    urdf=validate_sources()
    links={link.get('name'):link for link in urdf.findall('link')}
    colors={material.get('name'):material.find('color').get('rgba') for material in urdf.findall('.//material') if material.find('color') is not None}
    children={}
    for joint in urdf.findall('joint'):
        children.setdefault(joint.find('parent').get('link'),[]).append(joint)
    root=ET.Element('body',name='robot',pos='0 -20 .48')
    ET.SubElement(root,'freejoint',name='root')
    def populate(body,link_name):
        link=links[link_name]
        inertial=link.find('inertial')
        if inertial is not None:
            inertia=inertial.find('inertia')
            values=[inertia.get(k) for k in ('ixx','iyy','izz','ixy','ixz','iyz')]
            # The source inertial rotations are identity; preserve full inertia tensor.
            ET.SubElement(body,'inertial',pos=inertial.find('origin').get('xyz','0 0 0'),mass=inertial.find('mass').get('value'),fullinertia=' '.join(values))
        for index,visual in enumerate(link.findall('visual')):
            mesh=visual.find('geometry/mesh')
            if mesh is None:
                continue  # Reported as missing mesh visuals; never synthesized.
            color=visual.find('material/color')
            ET.SubElement(body,'geom',name=f'source_visual_{link_name}_{index}',type='mesh',mesh='mesh_'+Path(mesh.get('filename')).stem,rgba=color.get('rgba') if color is not None else colors.get(visual.find('material').get('name') if visual.find('material') is not None else '', '.5 .5 .5 1'),contype='0',conaffinity='0',density='0',**origin_attributes(visual.find('origin')))
        if link_name.endswith(('_coxa','_femur','_tibia')):
            # Only authorized visual addition: replacement motor at the existing pivot,
            # with its shaft axis aligned to that joint's source URDF axis.
            quat='1 0 0 0' if link_name.endswith('_coxa') else '.7071067811865476 0 .7071067811865476 0'
            ET.SubElement(body,'geom',name='actuator_'+link_name,type='mesh',mesh='mesh_rs04_actuator',pos='0 0 0',quat=quat,rgba='.12 .12 .14 1',contype='0',conaffinity='0',density='0')
        # Original URDF collision proxies are invisible and are not visual substitutes.
        for index,collision in enumerate(link.findall('collision')):
            geometry=collision.find('geometry');attrs={}
            if geometry.find('box') is not None:
                attrs=dict(type='box',size=' '.join(str(float(v)/2) for v in geometry.find('box').get('size').split()))
            elif geometry.find('cylinder') is not None:
                shape=geometry.find('cylinder');attrs=dict(type='cylinder',size=f'{shape.get("radius")} {float(shape.get("length"))/2}')
            elif geometry.find('sphere') is not None:
                attrs=dict(type='sphere',size=geometry.find('sphere').get('radius'))
            if attrs:
                ET.SubElement(body,'geom',name=f'source_collision_{link_name}_{index}',group='3',contype='2',conaffinity='1',density='0',**attrs,**origin_attributes(collision.find('origin')))
        for joint in children.get(link_name,[]):
            child_name=joint.find('child').get('link')
            child=ET.SubElement(body,'body',name=child_name,**origin_attributes(joint.find('origin')))
            if joint.get('type')!='fixed':
                limits=joint.find('limit');dynamics=joint.find('dynamics')
                ET.SubElement(child,'joint',name=joint.get('name'),type='hinge',axis=joint.find('axis').get('xyz'),range=f'{limits.get("lower")} {limits.get("upper")}',damping=dynamics.get('damping','0') if dynamics is not None else '0')
            populate(child,child_name)
    populate(root,'base_link')
    return ET.tostring(root,encoding='unicode')


def finalize_source_robot(root):
    # Only supplied geometry, units, original colors and source assembly transforms.
    referenced={g.get('mesh') for g in root.findall(".//body[@name='robot']//geom") if g.get('mesh')}
    for mesh in root.findall('asset/mesh'):
        if mesh.get('name','').startswith('mesh_') and mesh.get('name') not in referenced:
            root.find('asset').remove(mesh)
            continue
        if mesh.get('name','').startswith('mesh_'):
            filename=mesh.get('file')
            mesh.set('file',str(ACTUATOR_REPLACEMENT if mesh.get('name')=='mesh_rs04_actuator' else SOURCE_MESH_DIR/Path(filename).name))
    old=root.find('actuator')
    if old is not None:
        root.remove(old)
    actuators=ET.SubElement(root,'actuator')
    for joint in validate_sources().findall('joint'):
        if joint.get('type')=='fixed':continue
        limit=joint.find('limit')
        ET.SubElement(actuators,'position',name='source_act_'+joint.get('name'),joint=joint.get('name'),kp='450',kv='35',forcerange=f'-{limit.get("effort")} {limit.get("effort")}',ctrlrange=f'{limit.get("lower")} {limit.get("upper")}')


def write_report(path):
    validate_sources()
    report={
        'source_directory':str(SOURCE_MESH_DIR),
        'mesh_sha256':{name:hashlib.sha256((SOURCE_MESH_DIR/name).read_bytes()).hexdigest() for name in REQUIRED_MESHES},
        'mission_mode':'walking only; wheels intentionally excluded',
        'errors':[],
        'actuator_replacement':json.loads((ACTUATOR_REPLACEMENT.parent/'actuator_provenance.json').read_text()),
        'actuator_mounting':'18 motor visuals at existing URDF joint pivots; shaft aligned to each joint axis. No other source geometry or link transforms changed.',
        'foot_policy':'Source URDF foot spheres remain collision-only; no added foot visuals.',
        'visual_policy':'20 original URDF mesh visuals unchanged, plus 18 instances of the authorized actuator replacement. Original source STL files and URDF are unchanged.'
    }
    Path(path).write_text(json.dumps(report,indent=2))
    return report
