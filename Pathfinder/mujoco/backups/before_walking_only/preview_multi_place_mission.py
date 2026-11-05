#!/usr/bin/env python3
"""Interactive CAD hexapod mission preview with assisted chassis stabilization.

C: camera; M: wheels/legs; B: 18% low-battery test; 1-4: dispatch; 0: charge.
Scene-derived A* uses a 1.82m swept robot radius and checks braking clearance.
Tripod inverse kinematics plants stance feet and eases swing endpoints.
At <=35% battery, the mission diverts through [0,-4] to the charger [0,1.2].
Charging reaches 100% and holds green for 2.4s before mission resumption.

This is a navigation/design preview: chassis velocity and attitude remain
assisted, and the illustrated LiDAR is not used as a live perception sensor.
"""

import sys
import math
import time
import subprocess
import argparse
import json
from contextlib import nullcontext
from types import SimpleNamespace
from pathlib import Path
from safe_navigation import SafeNavigator
from tripod_gait import TripodGait, clear_transform_feet
from collections import deque
import numpy as np
import mujoco
import mujoco.viewer

from multi_place_config import (
    DEST_BASE,
    DEST_PLACE_1,
    DEST_PLACE_2,
    DEST_PLACE_3,
    DEST_PLACE_4,
    DEST_KIOSK_PAD,
    DEST_KIOSK_ENTRY,
    DEST_KIOSK,
    MISSION_TARGETS,
    KIOSK_RECHARGE_TARGET,
    NON_TRAVERSABLE_OBSTACLES,
    TRAVERSABLE_OBSTACLES,
    SMALL_PATH_OBSTACLES,
    ZONE_BBOX_MUD,
    ZONE_BBOX_ROCKY,
    ZONE_BBOX_FOREST,
    ZONE_BBOX_SAND,
    get_kiosk_departure_corridor,
)

ALL_OBSTACLES = list(NON_TRAVERSABLE_OBSTACLES)



def get_roll_pitch_yaw(d):
    qw, qx, qy, qz = d.qpos[3:7]
    sinr_cosp = 2.0 * (qw * qx + qy * qz)
    cosr_cosp = 1.0 - 2.0 * (qx * qx + qy * qy)
    roll = math.atan2(sinr_cosp, cosr_cosp)

    sinp = 2.0 * (qw * qy - qz * qx)
    if abs(sinp) >= 1.0:
        pitch = math.copysign(math.pi / 2.0, sinp)
    else:
        pitch = math.asin(sinp)

    siny_cosp = 2.0 * (qw * qz + qx * qy)
    cosy_cosp = 1.0 - 2.0 * (qy * qy + qz * qz)
    yaw = math.atan2(siny_cosp, cosy_cosp)
    return roll, pitch, yaw


def norm_ang(a):
    while a > math.pi:
        a -= 2.0 * math.pi
    while a < -math.pi:
        a += 2.0 * math.pi
    return a


def is_in_bbox(x, y, bbox):
    """Check if point (x, y) is inside bounding box [xmin, xmax, ymin, ymax]."""
    return (bbox[0] <= x <= bbox[1]) and (bbox[2] <= y <= bbox[3])


def get_kiosk_approach_corridor(curr_pos):
    """
    Computes an obstacle-free corridor to the Battery Charging Station that ALWAYS
    enters strictly through the front middle entrance (DEST_KIOSK_ENTRY [0.0, -4.0])
    along the yellow chevron runway, preventing any collision with side pillars/bollards.
    Routes strictly via wide open fairways to avoid interior camp or quarry obstacles,
    and safely bypasses the Kiosk building from the north via lateral arterial highways.
    """
    rx, ry = float(curr_pos[0]), float(curr_pos[1])
    corridor = []

    if ry > 2.0:
        # North of kiosk: Route south along west or east highway down to y = -4.0
        side_x = -10.0 if rx <= 0.0 else 10.0
        if abs(rx) > 11.5:
            corridor.append(np.array([side_x, 16.0], dtype=np.float32))

        # Dense highway waypoints heading south towards y = -4.0
        for y_step in np.arange(min(ry, 16.0), -4.1, -3.0):
            corridor.append(np.array([side_x, float(y_step)], dtype=np.float32))
        corridor.append(np.array([side_x, -4.0], dtype=np.float32))
        corridor.append(np.array([side_x * 0.5, -4.0], dtype=np.float32))
    elif rx <= -3.0 and ry <= 0.0:
        corridor.append(np.array([-10.0, -10.0], dtype=np.float32))
        corridor.append(np.array([-10.0, -7.0], dtype=np.float32))
        corridor.append(np.array([-10.0, -4.0], dtype=np.float32))
        corridor.append(np.array([-5.0, -4.0], dtype=np.float32))
    elif rx >= 3.0 and ry <= 0.0:
        corridor.append(np.array([10.0, -10.0], dtype=np.float32))
        corridor.append(np.array([10.0, -7.0], dtype=np.float32))
        corridor.append(np.array([10.0, -4.0], dtype=np.float32))
        corridor.append(np.array([5.0, -4.0], dtype=np.float32))
    elif ry <= -6.0:
        for y_step in np.arange(ry, -4.1, 3.0):
            corridor.append(np.array([0.0, float(y_step)], dtype=np.float32))

    # ALWAYS route through front middle entrance first, then drive up the runway onto pad
    corridor.append(DEST_KIOSK_ENTRY)
    corridor.append(DEST_KIOSK_PAD)
    return corridor


def spawn_window_bring_to_front():
    """Launch detached helper process to position window once created."""
    helper_code = '''
import time, ctypes
time.sleep(1.8)
try:
    x11 = ctypes.cdll.LoadLibrary("libX11.so.6")
    x11.XOpenDisplay.restype = ctypes.c_void_p
    display = x11.XOpenDisplay(b":1")
    if display:
        root = x11.XDefaultRootWindow(display)
        def find_mujoco(w):
            name_ptr = ctypes.c_char_p()
            if x11.XFetchName(display, ctypes.c_ulong(w), ctypes.byref(name_ptr)) != 0:
                if name_ptr.value and b"MuJoCo" in name_ptr.value:
                    return w
            root_ret, parent_ret = ctypes.c_ulong(), ctypes.c_ulong()
            children = ctypes.POINTER(ctypes.c_ulong)()
            nchildren = ctypes.c_uint()
            status = x11.XQueryTree(display, ctypes.c_ulong(w), ctypes.byref(root_ret),
                                    ctypes.byref(parent_ret), ctypes.byref(children), ctypes.byref(nchildren))
            found = None
            if status != 0 and nchildren.value > 0:
                for i in range(nchildren.value):
                    res = find_mujoco(children[i])
                    if res:
                        found = res
                        break
                x11.XFree(children)
            return found

        target_w = find_mujoco(root)
        if target_w:
            x11.XMapRaised(display, target_w)
            x11.XFlush(display)
            x11.XCloseDisplay(display)
except Exception as e:
    pass
'''
    subprocess.Popen([sys.executable, "-c", helper_code])


def run_mission(args=None):
    from strict_asset import validate_sources
    validate_sources(require_hybrid=True)
    args = args or SimpleNamespace(headless=False, steps=0, battery_test_step=0, dispatch=1, report=None)
    xml_path = str(Path(__file__).with_name("hybrid_hexapod_multi_place.xml"))
    m = mujoco.MjModel.from_xml_path(xml_path)
    d = mujoco.MjData(m)
    wheel_dofs = [int(m.joint(name+"_joint").dofadr[0]) for name in ("wheel_FL","wheel_FR","wheel_RL","wheel_RR")]

    beacon_mat_id = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_MATERIAL, "battery_light")
    halo_mat_id = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_MATERIAL, "battery_halo_mat")
    scan_core_mat_id = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_MATERIAL, "scan_core_mat")

    # High-Resolution 3D LiDAR Visual Materials
    lidar_laser_mat_id = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_MATERIAL, "lidar_laser_mat")
    lidar_cone_mat_id = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_MATERIAL, "lidar_cone_mat")
    lidar_ring_mat_id = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_MATERIAL, "lidar_wave_ring_mat")

    # 5-Segment LED battery gauge material IDs
    bat_led_ids = []
    for i in range(1, 6):
        mat_id = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_MATERIAL, f"bat_led_mat_{i}")
        bat_led_ids.append(mat_id)

    # Initial robot posture: resting on 4 wheels at Base Depot [0.0, -20.0] facing North (+Y)
    d.qpos[0] = float(DEST_BASE[0])
    d.qpos[1] = float(DEST_BASE[1])
    d.qpos[2] = 0.240  # Chassis height directly on all-terrain rubber wheels
    d.qpos[3:7] = [0.7071068, 0.0, 0.0, 0.7071068]  # Facing North along arterial outbound highway

    # Legs naturally stowed in compact fold alongside chassis flanks (hooks locked in top cover side pockets)
    INIT_STOW = np.array([
         0.00,  1.047, -2.00,  # LF: Tucked alongside flank, hook locked in left pocket
         0.00,  1.047, -2.00,  # LM: Tucked alongside flank, hook locked in left pocket
         0.00,  1.047, -2.00,  # LR: Tucked alongside flank, hook locked in left pocket
         0.00,  1.047, -2.00,  # RF: Tucked alongside flank, hook locked in right pocket
         0.00,  1.047, -2.00,  # RM: Tucked alongside flank, hook locked in right pocket
         0.00,  1.047, -2.00,  # RR: Tucked alongside flank, hook locked in right pocket
    ], dtype=np.float32)
    d.qpos[12:30] = INIT_STOW
    d.ctrl[4:22] = INIT_STOW
    mujoco.mj_step(m, d)

    print("=" * 86, flush=True)
    print("🚀 ADVANCED HYBRID HEXAPOD EXPEDITION: BIOMIMETIC WALKING & EXPANDED BIOMES", flush=True)
    print("=" * 86, flush=True)
    print("🗺️  Mission Architecture (Hub-and-Spoke with Full Perimeter Circuits):", flush=True)
    print("  • Origin Base Camp [0.0, -20.0]: Staging hub visited after each site scan (NOT charging):", flush=True)
    print("    Base -> Place 1 (Full 360° Round) -> Base -> Place 2 (Full 360° Round) -> ...", flush=True)
    print("  • Dedicated Battery Charging Station (Pad [0.0, 1.2]):", flush=True)
    print("    Low-Battery Override (<= 35% RED) -> Diverts directly via middle entrance [0.0, -4.0]!", flush=True)
    print("    Dwells until SOLID GREEN 🟢 before departing; NEVER charges at Base Depot!", flush=True)
    print("🐾 Realistic Biomimetic Hexapod Walking Gait (0.95 Hz):", flush=True)
    print("  • Ground-referenced inverse kinematics, planted stance feet and smooth swing lift", flush=True)
    print("🏎️  Silky Smooth Wheel Locomotion:", flush=True)
    print("  • Wheel angular velocity follows commanded speed; chassis height and attitude are assisted", flush=True)
    print("📡 High-Resolution 3D LiDAR Visualization:", flush=True)
    print("  • 7-Beam high-emission neon cyan laser fan (4.5m range, 90° arc) + ground ripple wave rings", flush=True)
    print("🎮 INTERACTIVE CONTROLS:", flush=True)
    print("  • Mouse Drag / Scroll: Free Camera Orbit, Zoom & Pan (Zero Lockout!)", flush=True)
    print("  • K: Toggle Autonomous Mission <-> Manual Keyboard Drive Mode (Space reserved for viewer pause)", flush=True)
    print("  • WASD / Arrow Keys: Drive & Steer Robot Manually", flush=True)
    print("  • M: Toggle Morphing Mode (4-Wheel Drive <-> 6-Legged Walker)", flush=True)
    print("  • C: Cycle Camera Views (Tracking Chase <-> Overhead Map <-> Close-up)", flush=True)
    print("  • R: Reset / Realign Robot to Base Depot Apron [0.0, -20.0]", flush=True)
    print("=" * 86, flush=True)

    if not args.headless:
        spawn_window_bring_to_front()

    # Mission state variables
    target_idx = 0
    mission_stage = "approach"  # "approach", "circuit", "return"
    corridor = MISSION_TARGETS[0]["approach"]
    corridor_idx = 0
    waypoint_stall_count = 0
    phase = 0  # 0: Cruising/Walking, 1: Station Recharging, 2: Site Scan Dwell, 3: Base Depot Dwell
    battery = 100.0

    # Low-Battery Override State
    is_recharge_divert = False
    interrupted_target_idx = 0
    interrupted_stage = "approach"
    interrupted_corridor = []
    interrupted_corridor_idx = 0
    resume_circuit = None
    recharge_counter = 0
    recharge_total = int(2.4 / 0.016)  # ~3.5 seconds snappy dwell on charging pad

    scan_dwell_counter = 0
    scan_dwell_total = int(0.60 / 0.016)  # ~0.60 seconds LiDAR sector scan dwell

    base_dwell_counter = 0
    base_dwell_total = int(0.90 / 0.016)  # ~0.90 seconds base staging pause (telemetry sync)

    in_walking_mode = False
    morph_alpha = 0.0  # Smooth morphing parameter: 0.0 (Wheels) <-> 1.0 (6-Legged Tripod)
    walk_step_count = 0
    chassis_z_curr = 0.240
    step = 0
    lap_count = 1
    total_collisions = 0
    min_obstacle_dist = 999.0
    last_color_state = ""
    start_time = time.time()

    # Smooth velocity & steering filters
    v_smooth = 0.0
    omega_smooth = 0.0
    v_target = 0.0
    omega_target = 0.0
    err_yaw = 0.0

    # Anti-Stall displacement & heading tracker (rolling 50-step history ~0.8s)
    pos_history = deque(maxlen=75)
    stall_steps = 0
    escape_counter = 0
    escape_steer_dir = 1.0

    # Evasion side memory for hysteresis
    evasion_side = {}

    # Interactive manual driving & camera state
    manual_mode = False
    manual_v = 0.0
    manual_omega = 0.0
    transform_counter = 0
    transform_duration = 100  # ~1.6s smooth visible multi-stage transformation sequence
    transform_cooldown = 0
    manual_morph_req = None
    last_key_time = 0.0
    cam_preset = 1  # Start in Overview Free Camera by default (Zero lockout, free pan/zoom)
    last_terrain_state = False

    def on_key(keycode):
        nonlocal resume_circuit, interrupted_target_idx, interrupted_stage, interrupted_corridor, interrupted_corridor_idx
        nonlocal manual_mode, manual_v, manual_omega, manual_morph_req, last_key_time, cam_preset, battery, is_recharge_divert, phase, target_idx, active_target, mission_stage, corridor, corridor_idx, waypoint_stall_count, morph_alpha, in_walking_mode, transform_counter, transform_duration, v_smooth, omega_smooth
        if keycode in (49,50,51,52) and battery <= 35.0:
            print("Battery low: finish charging before dispatching to a place.", flush=True)
            return
        if keycode in (48,49,50,51,52):
            manual_mode = False
            manual_v = manual_omega = 0.0
        if keycode in (49,50,51,52):
            resume_circuit = None
        # K or k (75, 107): Toggle Autonomous <-> Manual Drive (Space reserved for viewer pause)
        if keycode in (75, 107):
            manual_mode = not manual_mode
            if not manual_mode:
                manual_v = 0.0
                manual_omega = 0.0
            last_key_time = time.time()
            mode_name = "MANUAL KEYBOARD DRIVE (WASD / Arrows to drive!)" if manual_mode else "AUTONOMOUS MISSION LOOP"
            print(f"\n🎮 [CONTROL TOGGLE] Switched mode -> {mode_name}\n", flush=True)
        # W or Up Arrow (87, 119, 265): Drive Forward (Active only if manual_mode toggled via K)
        elif keycode in (87, 119, 265):
            if manual_mode:
                phase = 0
                manual_v = float(np.clip(manual_v + 0.45, 0.45, 1.25))
                last_key_time = time.time()
                print(f"🎮 [DRIVE] Forward -> {manual_v:.2f} m/s", flush=True)
        # S or Down Arrow (83, 115, 264): Reverse
        elif keycode in (83, 115, 264):
            if manual_mode:
                phase = 0
                manual_v = float(np.clip(manual_v - 0.45, -0.90, -0.45))
                last_key_time = time.time()
                print(f"🎮 [DRIVE] Reverse -> {manual_v:.2f} m/s", flush=True)
        # A or Left Arrow (65, 97, 263): Steer Left
        elif keycode in (65, 97, 263):
            if manual_mode:
                phase = 0
                manual_omega = float(np.clip(manual_omega + 0.55, 0.45, 1.50))
                last_key_time = time.time()
                print(f"🎮 [STEER] Left -> {manual_omega:.2f} rad/s", flush=True)
        # D or Right Arrow (68, 100, 262): Steer Right
        elif keycode in (68, 100, 262):
            if manual_mode:
                phase = 0
                manual_omega = float(np.clip(manual_omega - 0.55, -1.50, -0.45))
                last_key_time = time.time()
                print(f"🎮 [STEER] Right -> {manual_omega:.2f} rad/s", flush=True)
        # M or m (77, 109): Trigger Dedicated Transformation Sequence (Wheels <-> 6 Legs)
        elif keycode in (77, 109):
            if in_walking_mode or morph_alpha > 0.5:
                phase = 5  # MORPH_TO_WHEELS
                transform_counter = 0
                v_smooth = 0.0
                omega_smooth = 0.0
                print("\n🏎️  [TRANSFORMATION COMMAND] Initiating transition to FRONT/REAR WHEELED DRIVE (Docking hooks in side pockets)...\n", flush=True)
            else:
                phase = 4  # MORPH_TO_LEGS
                transform_counter = 0
                v_smooth = 0.0
                omega_smooth = 0.0
                print("\n🐾 [TRANSFORMATION COMMAND] Initiating transition to 6-LEGGED TRIPOD GAIT (Unhooking legs & elevating chassis)...\n", flush=True)
        # O or o (79, 111): Direct Jump to Tactical Overview View (Full 72m arena)
        elif keycode in (79, 111):
            cam_preset = 1
            viewer.cam.type = mujoco.mjtCamera.mjCAMERA_FREE
            viewer.cam.lookat[0] = 0.0
            viewer.cam.lookat[1] = -5.0
            viewer.cam.lookat[2] = 1.0
            viewer.cam.distance = 45.0
            viewer.cam.elevation = -48.0
            viewer.cam.azimuth = 90.0
            print("\n📷 [OVERVIEW CAMERA ACTIVATED] Full 72m arena framed! Zero lockout: Middle-drag (or Shift+Left drag) pan anywhere, Left-drag orbit, Right-drag zoom.\n", flush=True)
        # T or t (84, 116): Direct Jump to Smooth Tracking Chase View
        elif keycode in (84, 116):
            cam_preset = 0
            viewer.cam.type = mujoco.mjtCamera.mjCAMERA_TRACKING
            viewer.cam.trackbodyid = m.body('robot').id
            viewer.cam.distance = 4.2
            viewer.cam.elevation = -22.0
            viewer.cam.azimuth = 90.0
            print("\n📷 [TRACKING CAMERA ACTIVATED] Following hexapod robot! Left-drag to orbit around robot, Right-drag to zoom.\n", flush=True)
        # F or f (70, 102): Direct Jump to Free Camera View
        elif keycode in (70, 102):
            cam_preset = 2
            viewer.cam.type = mujoco.mjtCamera.mjCAMERA_FREE
            viewer.cam.lookat[0] = float(d.qpos[0])
            viewer.cam.lookat[1] = float(d.qpos[1])
            viewer.cam.lookat[2] = float(d.qpos[2]) + 0.2
            viewer.cam.distance = 9.0
            viewer.cam.elevation = -30.0
            print("\n📷 [FREE CAMERA ACTIVATED] Unlocked camera centered on hexapod! Middle-drag pan anywhere across the 72m world without snapping back.\n", flush=True)
        # R or r (82, 114): Complete Mission Reset to Base Depot
        elif keycode in (82, 114):
            d.qpos[0] = float(DEST_BASE[0])
            d.qpos[1] = float(DEST_BASE[1])
            d.qpos[2] = 0.240
            d.qpos[3:7] = [0.7071068, 0.0, 0.0, 0.7071068]
            d.qvel[:] = 0.0
            manual_mode = False
            manual_v = 0.0
            manual_omega = 0.0
            phase = 0
            target_idx = 0
            active_target = MISSION_TARGETS[0]
            mission_stage = "approach"
            corridor = active_target["approach"]
            corridor_idx = 0
            waypoint_stall_count = 0
            battery = 100.0
            is_recharge_divert = False
            morph_alpha = 0.0
            in_walking_mode = False
            print(f"\n🔄 [RESET] Full expedition mission loop reset to Base Depot Staging Apron [{DEST_BASE[0]:.1f}, {DEST_BASE[1]:.1f}]!\n", flush=True)
        # B or b (66, 98): Force low-battery test (trigger recharge diversion to kiosk pad)
        elif keycode in (66, 98):
            battery = 18.0
            print("\n🪫 [MANUAL OVERRIDE] Battery drained to 18% (Critical Red) -> Diverting to Kiosk!\n", flush=True)
        # 1 (49): Instant Dispatch to Place 1 (Pine Forest & Science Camp)
        elif keycode == 49:
            target_idx = 0
            active_target = MISSION_TARGETS[0]
            mission_stage = "approach"
            corridor = active_target["approach"]
            corridor_idx = 0
            waypoint_stall_count = 0
            phase = 0
            is_recharge_divert = False
            print("\n🌲 [DISPATCH KEY 1] Immediate autonomous dispatch to Place 1: Dense Pine Forest & Science Camp!\n", flush=True)
        # 2 (50): Instant Dispatch to Place 2 (Granite Quarry & Ore Basin)
        elif keycode == 50:
            target_idx = 1
            active_target = MISSION_TARGETS[1]
            mission_stage = "approach"
            corridor = active_target["approach"]
            corridor_idx = 0
            waypoint_stall_count = 0
            phase = 0
            is_recharge_divert = False
            print("\n⛏️  [DISPATCH KEY 2] Immediate autonomous dispatch to Place 2: Granite Quarry & Mineral Basin!\n", flush=True)
        # 3 (51): Instant Dispatch to Place 3 (Mud Marsh & Wetland Estuary)
        elif keycode == 51:
            target_idx = 2
            active_target = MISSION_TARGETS[2]
            mission_stage = "approach"
            corridor = active_target["approach"]
            corridor_idx = 0
            waypoint_stall_count = 0
            phase = 0
            is_recharge_divert = False
            print("\n🌿 [DISPATCH KEY 3] Immediate autonomous dispatch to Place 3: Wet Mud Marsh & Lagoon Estuary!\n", flush=True)
        # 4 (52): Instant Dispatch to Place 4 (Golden Sand Dunes & Ruins)
        elif keycode == 52:
            target_idx = 3
            active_target = MISSION_TARGETS[3]
            mission_stage = "approach"
            corridor = active_target["approach"]
            corridor_idx = 0
            waypoint_stall_count = 0
            phase = 0
            is_recharge_divert = False
            print("\n🏛️  [DISPATCH KEY 4] Immediate autonomous dispatch to Place 4: Golden Sand Dunes & Ancient Ruins!\n", flush=True)
        # 0 (48): Instant Dispatch to Honda Battery Swap Station
        elif keycode == 48:
            is_recharge_divert = True
            interrupted_target_idx = target_idx
            interrupted_stage = mission_stage
            interrupted_corridor = list(corridor)
            interrupted_corridor_idx = corridor_idx
            curr_xy = np.array([float(d.qpos[0]), float(d.qpos[1])])
            corridor = get_kiosk_approach_corridor(curr_xy)
            corridor_idx = 0
            waypoint_stall_count = 0
            phase = 0
            print("\n🔋 [DISPATCH KEY 0] Diverting straight to Honda e:Swap Battery Station!\n", flush=True)
        # C or c (67, 99): Cycle Camera Presets
        elif keycode in (67, 99):
            cam_preset = (cam_preset + 1) % 4
            if cam_preset == 0:
                viewer.cam.type = mujoco.mjtCamera.mjCAMERA_TRACKING
                viewer.cam.trackbodyid = m.body('robot').id
                viewer.cam.distance = 4.2
                viewer.cam.elevation = -22.0
                print("\n📷 [CAMERA 1/4: TRACKING CHASE] Following robot closely (Orbit/Zoom enabled)\n", flush=True)
            elif cam_preset == 1:
                viewer.cam.type = mujoco.mjtCamera.mjCAMERA_FREE
                viewer.cam.lookat[0] = 0.0
                viewer.cam.lookat[1] = -5.0
                viewer.cam.lookat[2] = 1.0
                viewer.cam.distance = 45.0
                viewer.cam.elevation = -48.0
                viewer.cam.azimuth = 90.0
                print("\n📷 [CAMERA 2/4: ARENA OVERVIEW] High-altitude 72m arena map (Free Pan/Zoom/Orbit enabled)\n", flush=True)
            elif cam_preset == 2:
                viewer.cam.type = mujoco.mjtCamera.mjCAMERA_FREE
                viewer.cam.lookat[0] = float(d.qpos[0])
                viewer.cam.lookat[1] = float(d.qpos[1])
                viewer.cam.lookat[2] = 0.3
                viewer.cam.distance = 9.0
                viewer.cam.elevation = -30.0
                print("\n📷 [CAMERA 3/4: FREE ORBIT] Free Camera (Pan/Zoom/Orbit anywhere)\n", flush=True)
            elif cam_preset == 3:
                viewer.cam.type = mujoco.mjtCamera.mjCAMERA_TRACKING
                viewer.cam.trackbodyid = m.body('robot').id
                viewer.cam.distance = 1.8
                viewer.cam.elevation = -12.0
                print("\n📷 [CAMERA 4/4: CLOSE-UP INSPECTION] High-detail chassis & leg articulation view\n", flush=True)

    navigator = SafeNavigator(m, d)
    gait = TripodGait()
    safety_stops = 0
    min_surface_clearance = float('inf')
    route_failures = 0
    obstacle_contact_substeps = 0
    max_body_tilt = 0.0
    minimum_foot_bottom = 1.0
    charge_completed = 0
    visited_places = set()
    if args.headless:
        class HeadlessViewer:
            def __init__(self):
                self.cam = mujoco.MjvCamera()
            def is_running(self):
                return step < args.steps
            def sync(self):
                pass
        context = nullcontext(HeadlessViewer())
    else:
        context = mujoco.viewer.launch_passive(m, d, key_callback=on_key)
    with context as viewer:
        if args.dispatch != 1:
            on_key(48 + args.dispatch)
        viewer.cam.type = mujoco.mjtCamera.mjCAMERA_FREE
        viewer.cam.lookat[0] = 0.0
        viewer.cam.lookat[1] = -5.0
        viewer.cam.lookat[2] = 1.0
        viewer.cam.distance = 45.0
        viewer.cam.elevation = -48.0
        viewer.cam.azimuth = 90.0

        prev_pos = np.array([float(d.qpos[0]), float(d.qpos[1])])

        while viewer.is_running():
            step_start = time.time()
            step += 1
            if args.battery_test_step and step == args.battery_test_step:
                on_key(66)

            rx, ry = float(d.qpos[0]), float(d.qpos[1])
            curr_pos = np.array([rx, ry])
            roll, pitch, yaw = get_roll_pitch_yaw(d)

            # Record position and yaw for stall detection (ONLY while actively cruising in phase 0)
            if phase == 0 and escape_counter <= 0 and not manual_mode:
                pos_history.append((step, curr_pos.copy(), yaw))
            else:
                pos_history.clear()
                stall_steps = 0

            # Distance traveled in this physics step
            ds = float(np.linalg.norm(curr_pos - prev_pos))
            prev_pos = curr_pos.copy()

            # -------------------------------------------------------------
            # 1. ACTIVE 3D SWEEPING LIDAR TURRET & DYNAMIC VISUAL FAN
            # (Shuts down immediately during recharge divert or critical battery)
            # -------------------------------------------------------------
            is_active_scanning = ((mission_stage == "circuit") or (phase == 2)) and not is_recharge_divert and battery > 35.0
            if is_active_scanning:
                # Fast sweeping turret swivel (+/-72 degrees at 0.85 Hz)
                scan_angle = 1.25 * math.sin(step * 0.45)
                d.ctrl[22] = scan_angle

                pulse_beam = 0.75 + 0.22 * math.sin(step * 0.35)
                pulse_ring = 0.45 + 0.30 * math.cos(step * 0.40)
                pulse_cone = 0.22 + 0.10 * math.sin(step * 0.50)

                m.mat_rgba[lidar_laser_mat_id] = [0.05, 0.98, 0.92, pulse_beam]
                m.mat_rgba[lidar_ring_mat_id] = [0.05, 0.98, 0.92, pulse_ring]
                m.mat_rgba[lidar_cone_mat_id] = [0.05, 0.98, 0.92, pulse_cone]
                m.mat_rgba[scan_core_mat_id] = [0.10, 0.98, 0.95, 1.0]

            else:
                # Standby cruising mode
                d.ctrl[22] = 0.35 * math.sin(step * 0.12)
                m.mat_rgba[lidar_laser_mat_id] = [0.05, 0.98, 0.92, 0.10]
                m.mat_rgba[lidar_ring_mat_id] = [0.05, 0.98, 0.92, 0.04]
                m.mat_rgba[lidar_cone_mat_id] = [0.05, 0.98, 0.92, 0.02]
                m.mat_rgba[scan_core_mat_id] = [0.10, 0.85, 0.85, 0.8]

            # -------------------------------------------------------------
            # 2. CALIBRATED BATTERY CONSUMPTION & IMMEDIATE LOW-BATTERY OVERRIDE (<= 35%)
            # -------------------------------------------------------------
            if phase == 0:
                drain_rate = 0.20 if in_walking_mode else 0.12
                battery = max(8.0, battery - ds * drain_rate - 0.0006)
            elif phase == 2:
                battery = max(8.0, battery - 0.0008)

            # IMMEDIATE RED-LIGHT LOW-BATTERY DIVERT (<= 35.0%)
            # The moment battery hits <= 35%, beacon turns RED and robot IMMEDIATELY diverts to Kiosk!
            if battery <= 35.0 and not is_recharge_divert:
                is_recharge_divert = True
                manual_mode = False
                interrupted_target_idx = target_idx
                interrupted_stage = mission_stage
                interrupted_corridor = corridor
                interrupted_corridor_idx = corridor_idx

                # Abort any active scan dwell immediately
                if phase == 2:
                    phase = 0

                # Build safe corridor entering strictly through front middle entrance [0.0, -1.8]
                corridor = get_kiosk_approach_corridor(curr_pos)
                corridor_idx = 0

                print("\n" + "!" * 86, flush=True)
                print(f"🚨 [Step {step:05d}] LOW BATTERY RED ALERT ({battery:.1f}%)! CRITICAL THRESHOLD REACHED (<= 35%)!", flush=True)
                print(f"⚡ IMMEDIATE OVERRIDE: DIVERTING STRAIGHT TO BATTERY CHARGING STATION VIA {DEST_KIOSK_ENTRY}!", flush=True)
                print("🛑 (Expedition paused; robot heads straight to Kiosk to swap depleted battery pack, NOT to Origin Point!)", flush=True)
                print("!" * 86 + "\n", flush=True)

            # -------------------------------------------------------------
            # 3. DYNAMIC BATTERY BEACON & 5-SEGMENT LED GAUGE
            # -------------------------------------------------------------
            led_off = [0.12, 0.14, 0.12, 0.40]
            m.mat_emission[beacon_mat_id] = 1.0
            m.mat_emission[halo_mat_id] = 0.80

            if phase == 1:
                # RECHARGING AT CENTRAL KIOSK PAD [0.0, 0.95]
                pulse = 0.85 + 0.15 * math.sin(step * 0.35)
                fill_count = int(np.clip(battery / 20.0, 0, 5))

                if battery < 50.0:
                    # Depleted battery pack swapping
                    m.mat_rgba[beacon_mat_id] = [1.0 * pulse, 0.05, 0.05, 1.0]
                    m.mat_rgba[halo_mat_id] = [1.0, 0.05, 0.05, 0.45]
                    curr_color = "RED 🔴 (Cartridge Swapping...)"
                    active_led_col = [1.0, 0.05, 0.05, 1.0]
                elif battery < 85.0:
                    # High-current inductive charging
                    m.mat_rgba[beacon_mat_id] = [1.0, 0.65 * pulse, 0.05, 1.0]
                    m.mat_rgba[halo_mat_id] = [1.0, 0.65, 0.05, 0.40]
                    curr_color = "AMBER-ORANGE 🟠 (Inductive Fast-Charge...)"
                    active_led_col = [1.0, 0.65, 0.05, 1.0]
                elif battery < 99.5:
                    # Finishing balance charge
                    m.mat_rgba[beacon_mat_id] = [0.15 * pulse, 1.0, 0.25, 1.0]
                    m.mat_rgba[halo_mat_id] = [0.15, 1.0, 0.25, 0.45]
                    curr_color = "BRIGHT GREEN 🟢 (Cell Balancing...)"
                    active_led_col = [0.10, 1.0, 0.25, 1.0]
                else:
                    # 100% SOLID BRIGHT GREEN (CHARGE FINISH SIGNAL!)
                    m.mat_rgba[beacon_mat_id] = [0.05, 1.0, 0.20, 1.0]
                    m.mat_rgba[halo_mat_id] = [0.05, 1.0, 0.20, 0.60]
                    curr_color = "SOLID GREEN 🟢 (100% Charge Finished!)"
                    active_led_col = [0.05, 1.0, 0.20, 1.0]

                for idx in range(5):
                    if idx < fill_count:
                        m.mat_rgba[bat_led_ids[idx]] = active_led_col
                    elif idx == fill_count and battery < 99.5:
                        blink_val = 0.5 + 0.5 * math.sin(step * 0.4)
                        m.mat_rgba[bat_led_ids[idx]] = [active_led_col[0] * blink_val, active_led_col[1] * blink_val, active_led_col[2] * blink_val, 1.0]
                    else:
                        m.mat_rgba[bat_led_ids[idx]] = led_off

            elif phase == 3:
                # STAGING AT BASE DEPOT (ORIGIN POINT) - NOT CHARGING!
                m.mat_rgba[beacon_mat_id] = [0.10, 0.85, 0.45, 1.0]  # Nominal Health Green
                m.mat_rgba[halo_mat_id] = [0.10, 0.85, 0.45, 0.35]
                curr_color = "EMERALD GREEN 🟢 (Base Depot Staging)"
                fill_count = int(np.clip(battery / 20.0, 0, 5))
                led_c = [0.10, 0.85, 0.45, 1.0]
                for idx in range(5):
                    if idx < fill_count:
                        m.mat_rgba[bat_led_ids[idx]] = led_c
                    else:
                        m.mat_rgba[bat_led_ids[idx]] = led_off

            else:
                # NORMAL MISSION RUNNING
                fill_count = int(np.clip(battery / 20.0, 0, 5))

                if battery > 75.0:
                    m.mat_rgba[beacon_mat_id] = [0.10, 1.0, 0.25, 1.0]
                    m.mat_rgba[halo_mat_id] = [0.10, 1.0, 0.25, 0.35]
                    curr_color = "EMERALD GREEN 🟢 (Full - 100%)"
                    led_c = [0.10, 1.0, 0.25, 1.0]
                elif battery > 50.0:
                    m.mat_rgba[beacon_mat_id] = [0.55, 0.95, 0.15, 1.0]
                    m.mat_rgba[halo_mat_id] = [0.55, 0.95, 0.15, 0.35]
                    curr_color = "LIME GREEN 🟡 (Good)"
                    led_c = [0.55, 0.98, 0.15, 1.0]
                elif battery > 35.0:
                    m.mat_rgba[beacon_mat_id] = [1.0, 0.65, 0.05, 1.0]
                    m.mat_rgba[halo_mat_id] = [1.0, 0.65, 0.05, 0.40]
                    curr_color = "AMBER-ORANGE 🟠 (Mid-Charge)"
                    led_c = [1.0, 0.65, 0.05, 1.0]
                else:
                    # CRITICAL LOW BATTERY (<= 35%): PULSING BRIGHT NEON RED SIGNAL!
                    pulse = 0.6 + 0.4 * math.sin(step * 0.45)
                    m.mat_rgba[beacon_mat_id] = [1.0 * pulse, 0.02, 0.02, 1.0]
                    m.mat_rgba[halo_mat_id] = [1.0, 0.02, 0.02, 0.55]
                    curr_color = "CRITICAL RED 🔴 (BATTERY LOW - Heading to Kiosk!)"
                    led_c = [1.0, 0.05, 0.05, 1.0]

                for idx in range(5):
                    if idx < fill_count:
                        m.mat_rgba[bat_led_ids[idx]] = led_c
                    elif idx == fill_count and battery <= 35.0:
                        blink_val = 0.5 + 0.5 * math.sin(step * 0.50)
                        m.mat_rgba[bat_led_ids[idx]] = [led_c[0] * blink_val, led_c[1] * blink_val, led_c[2] * blink_val, 1.0]
                    else:
                        m.mat_rgba[bat_led_ids[idx]] = led_off

            if curr_color != last_color_state and phase == 0:
                print(f"💡 [Step {step:05d}] Battery telemetry update -> {curr_color} (Charge: {battery:.1f}%)", flush=True)
                last_color_state = curr_color

            # -------------------------------------------------------------
            # 4. ACTIVE TARGET RESOLUTION & FULL-CIRCUIT PROGRESSION
            # -------------------------------------------------------------
            if is_recharge_divert:
                active_target = KIOSK_RECHARGE_TARGET
                active_waypoint = corridor[corridor_idx]
                target_dest = DEST_KIOSK_PAD
            else:
                active_target = MISSION_TARGETS[target_idx]
                active_waypoint = corridor[corridor_idx]
                target_dest = active_target["pos"] if mission_stage == "approach" else active_waypoint

            dist_to_waypoint = float(np.linalg.norm(curr_pos - active_waypoint))
            dist_to_final = float(np.linalg.norm(curr_pos - target_dest))

            # Advance along current corridor
            adv_threshold = 0.55 if is_recharge_divert and corridor_idx == len(corridor) - 1 else (1.45 if mission_stage in ("circuit", "return") else 1.35)

            has_passed_waypoint = False
            adv_threshold = 0.30 if corridor_idx == len(corridor)-1 else 0.45

            if phase == 0 and (dist_to_waypoint < adv_threshold or has_passed_waypoint):
                if corridor_idx < len(corridor) - 1:
                    corridor_idx += 1
                    waypoint_stall_count = 0
                    active_waypoint = corridor[corridor_idx]
                    dist_to_waypoint = float(np.linalg.norm(curr_pos - active_waypoint))

                    # If in circuit stage, dwell briefly at each sector waypoint for high-res LiDAR scan
                    if mission_stage == "circuit" and not is_recharge_divert:
                        visited_places.add(target_idx + 1)
                        phase = 2
                        scan_dwell_counter = scan_dwell_total
                        v_smooth = 0.0
                        omega_smooth = 0.0
                        circuit_info = min(active_target["circuit"], key=lambda item: np.linalg.norm(item["pos"]-curr_pos))
                        print(f"📡 [Step {step:05d}] LiDAR SCAN: {circuit_info['label']}! Swiveling multi-beam fan...", flush=True)

                else:
                    # Reached final waypoint of current corridor
                    if is_recharge_divert:
                        # Arrived at Battery Charging Station (Kiosk Pad)
                        phase = 1
                        recharge_counter = recharge_total
                        v_smooth = 0.0
                        omega_smooth = 0.0
                        d.ctrl[0:4] = 0.0
                        d.qvel[0:6] = 0.0
                        print(f"\n🔋 [Step {step:05d}] DOCKED AT CENTRAL BATTERY EXCHANGE KIOSK!", flush=True)
                        print("   🛑 Robot halted cleanly on concrete pad under solar protective canopy.", flush=True)
                        print(f"   🤖 Swapping depleted cartridge ({battery:.1f}%) -> Monitoring until SOLID GREEN 🟢...", flush=True)

                    elif mission_stage == "return":
                        # Arrived at Origin Base Depot via return corridor
                        phase = 3
                        base_dwell_counter = base_dwell_total
                        v_smooth = 0.0
                        omega_smooth = 0.0
                        d.ctrl[0:4] = 0.0
                        d.qvel[0:6] = 0.0
                        print(f"\n🏠 [Step {step:05d}] RETURNED TO ORIGIN POINT (BASE DEPOT [0.0, -20.0])!", flush=True)
                        print(f"   📦 Synchronizing telemetry & offloading field samples (NOT CHARGING - Bat: {battery:.1f}%)...", flush=True)

                    elif mission_stage == "approach":
                        # Arrived at site entry -> Transition to full-circuit 360° perimeter scan loop!
                        mission_stage = "circuit"
                        corridor = resume_circuit if resume_circuit is not None else [pt["pos"] for pt in active_target["circuit"]]
                        resume_circuit = None
                        corridor_idx = 0
                        waypoint_stall_count = 0
                        phase = 2
                        scan_dwell_counter = scan_dwell_total
                        v_smooth = 0.0
                        omega_smooth = 0.0
                        print(f"\n📡 [Step {step:05d}] ARRIVED AT {active_target['name'].upper()}!", flush=True)
                        print(f"   🔄 INITIATING FULL 4-SECTOR 360° PERIMETER INSPECTION CIRCUIT WITH 3D LIDAR...", flush=True)

                    elif mission_stage == "circuit":
                        # Completed full interior 360° scan circuit inside site -> Transition to return corridor to Base Depot!
                        mission_stage = "return"
                        corridor = active_target["return_corridor"]
                        corridor_idx = 0
                        waypoint_stall_count = 0
                        print(f"\n✅ [Step {step:05d}] FULL INTERIOR SCAN CIRCUIT COMPLETED INSIDE {active_target['name'].upper()}!", flush=True)
                        print(f"   🛣️ Heading back to Origin Base Depot [0.0, -20.0] via shortest transit corridor...\n", flush=True)

            # -------------------------------------------------------------
            # 5. DWELL PHASE LOGIC (STATIONARY STATES)
            # -------------------------------------------------------------
            transforming_this_frame = phase in (4,5)
            if phase == 1:
                # Kiosk Recharging Dwell: charges to 100%, then holds solid green for ~150 steps (~2.4s)
                battery = min(100.0, battery + .25)
                if battery >= 100.0:
                    recharge_counter -= 1

                if step % 50 == 0:
                    fill_count = int(np.clip(battery / 20.0, 0, 5))
                    gauge_str = "🟩" * fill_count + "⬜" * (5 - fill_count)
                    print(f"   ⏳ [CHARGING STATION] Pad [0.0, 1.2] | Charge: {battery:.1f}% | Gauge: [{gauge_str}] | Beacon: {curr_color}", flush=True)

                if recharge_counter <= 0:
                    battery = 100.0
                    charge_completed += 1
                    phase = 0
                    if is_recharge_divert:
                        is_recharge_divert = False
                        target_idx = interrupted_target_idx
                        active_target = MISSION_TARGETS[target_idx]
                        if interrupted_stage == "return":
                            mission_stage = "return"
                            corridor = get_kiosk_departure_corridor(99)  # 99 routes directly to Base Depot
                            print(f"\n✅ [Step {step:05d}] LOW-BATTERY RECHARGE COMPLETE (100.0%)! BEACON SOLID EMERALD GREEN 🟢", flush=True)
                            print(f"🏁 Resuming return journey to Base Depot [0.0, -20.0] via central highway!\n", flush=True)
                        else:
                            mission_stage = interrupted_stage
                            corridor = list(get_kiosk_departure_corridor(target_idx))
                            if interrupted_stage == "circuit":
                                mission_stage = "approach"
                                resume_circuit = list(interrupted_corridor[interrupted_corridor_idx:])
                            print(f"\n✅ [Step {step:05d}] LOW-BATTERY RECHARGE COMPLETE (100.0%)! BEACON SOLID EMERALD GREEN 🟢", flush=True)
                            print(f"🏁 Smooth middle runway departure -> Resuming {active_target['name'].upper()}!\n", flush=True)
                    else:
                        # Automated Pitstop after Place 2 (Quarry) -> Advance to Place 3 (Mud Marsh)!
                        target_idx = 2  # Place 3 (Mud Marsh)
                        active_target = MISSION_TARGETS[target_idx]
                        mission_stage = "approach"
                        corridor = get_kiosk_departure_corridor(target_idx)
                        print(f"\n✅ [Step {step:05d}] PITSTOP RECHARGE COMPLETE (100.0%)! BEACON SOLID EMERALD GREEN 🟢", flush=True)
                        print(f"🏁 Smooth middle runway departure -> Proceeding to {active_target['name'].upper()}!\n", flush=True)
                    corridor_idx = 0
                    waypoint_stall_count = 0

            elif phase == 2:
                # Site Scan Sector Dwell
                scan_dwell_counter -= 1
                if scan_dwell_counter <= 0:
                    phase = 0
                    pos_history.clear()
                    stall_steps = 0

            elif phase == 3:
                # Base Depot Staging Dwell (NOT CHARGING - Field Staging Only!)
                base_dwell_counter -= 1
                if base_dwell_counter <= 0:
                    phase = 0
                    pos_history.clear()
                    stall_steps = 0
                    if target_idx == len(MISSION_TARGETS) - 1:
                        lap_count += 1
                        print(f"\n🏁 [Step {step:05d}] FULL 4-SITE EXPEDITION CYCLE COMPLETED AT BASE! Starting Lap {lap_count}...", flush=True)
                    target_idx = (target_idx + 1) % len(MISSION_TARGETS)
                    active_target = MISSION_TARGETS[target_idx]
                    mission_stage = "approach"
                    corridor = active_target["approach"]
                    corridor_idx = 0
                    print(f"🚀 [Step {step:05d}] DEPARTING BASE DEPOT -> HEADING TO {active_target['name'].upper()}!\n", flush=True)

            elif phase == 4:
                # DEDICATED PHACED TRANSFORMATION: WHEELS -> 6 ARTICULATED LEGS
                v_smooth = 0.0
                omega_smooth = 0.0
                d.ctrl[0:4] = 0.0
                d.qvel[0:6] = 0.0
                d.qvel[wheel_dofs] = 0.0
                transform_counter += 1
                tau = float(transform_counter) / float(transform_duration)

                if tau < 0.35:
                    # Stage 1: Unhook legs from top cover side pockets
                    # Femurs swing slightly down and out to release knee hooks from side pocket latches
                    s_unhook = math.sin(math.pi * (tau / 0.35))
                    cur_pose = STOW_POSE.copy()
                    cur_pose[1::3] = 1.047 - 0.25 * s_unhook
                    cur_pose[2::3] = -2.00 + 0.30 * s_unhook
                    chassis_z_curr = 0.240
                    morph_alpha = 0.0
                    d.ctrl[4:22] = cur_pose
                    d.qpos[12:30] = cur_pose
                elif tau < 0.70:
                    # Stage 2: Deploy legs outward and plant feet firmly on ground
                    s_dep = (tau - 0.35) / 0.35
                    s_dep_smooth = 0.5 - 0.5 * math.cos(math.pi * s_dep)
                    cur_pose = (1.0 - s_dep_smooth) * STOW_POSE + s_dep_smooth * NEUTRAL_STAND_POSE
                    chassis_z_curr = 0.240
                    morph_alpha = 0.5 * s_dep_smooth
                    d.ctrl[4:22] = cur_pose
                    d.qpos[12:30] = cur_pose
                else:
                    # Stage 3: Legs extend firmly, elevating chassis from 0.24m to 0.48m
                    s_elev = min(1.0, (tau - 0.70) / 0.30)
                    s_elev_smooth = 0.5 - 0.5 * math.cos(math.pi * s_elev)
                    chassis_z_curr = 0.240 + 0.240 * s_elev_smooth
                    morph_alpha = 0.5 + 0.5 * s_elev_smooth
                    d.ctrl[4:22] = NEUTRAL_STAND_POSE
                    d.qpos[12:30] = NEUTRAL_STAND_POSE

                if transform_counter >= transform_duration:
                    phase = 0
                    morph_alpha = 1.0
                    in_walking_mode = True
                    chassis_z_curr = 0.480
                    walk_step_count = 0
                    transform_cooldown = 150
                    print(f"✅ [Step {step:05d}] TRANSFORMATION TO LEGS COMPLETE! Elevated to 0.48m. Starting 6-legged tripod gait.\n", flush=True)

            elif phase == 5:
                # DEDICATED PHASED TRANSFORMATION: 6 LEGS -> FRONT/REAR WHEELS
                v_smooth = 0.0
                omega_smooth = 0.0
                d.ctrl[0:4] = 0.0
                d.qvel[0:6] = 0.0
                d.qvel[wheel_dofs] = 0.0
                transform_counter += 1
                tau = float(transform_counter) / float(transform_duration)

                if tau < 0.35:
                    # Stage 1: Lower chassis from 0.48m to 0.24m onto front & rear wheels
                    s_low = tau / 0.35
                    s_low_smooth = 0.5 - 0.5 * math.cos(math.pi * s_low)
                    chassis_z_curr = 0.480 - 0.240 * s_low_smooth
                    morph_alpha = 1.0 - 0.5 * s_low_smooth
                    d.ctrl[4:22] = NEUTRAL_STAND_POSE
                    d.qpos[12:30] = NEUTRAL_STAND_POSE
                elif tau < 0.70:
                    # Stage 2: Lift feet off ground, fold tibias tightly & swing femurs toward side pockets
                    s_fold = (tau - 0.35) / 0.35
                    s_fold_smooth = 0.5 - 0.5 * math.cos(math.pi * s_fold)
                    cur_pose = (1.0 - s_fold_smooth) * NEUTRAL_STAND_POSE + s_fold_smooth * STOW_POSE
                    cur_pose[1::3] = (1.0 - s_fold_smooth) * NEUTRAL_STAND_POSE[1::3] + s_fold_smooth * 0.90
                    cur_pose[2::3] = (1.0 - s_fold_smooth) * NEUTRAL_STAND_POSE[2::3] + s_fold_smooth * -2.00
                    chassis_z_curr = 0.240
                    morph_alpha = 0.5 * (1.0 - s_fold_smooth)
                    d.ctrl[4:22] = cur_pose
                    d.qpos[12:30] = cur_pose
                else:
                    # Stage 3: Lower femur hooks directly into top cover side pockets & lock
                    s_dock = min(1.0, (tau - 0.70) / 0.30)
                    s_dock_smooth = 0.5 - 0.5 * math.cos(math.pi * s_dock)
                    cur_pose = STOW_POSE.copy()
                    cur_pose[1::3] = 0.90 + (1.047 - 0.90) * s_dock_smooth
                    cur_pose[2::3] = -2.00
                    chassis_z_curr = 0.240
                    morph_alpha = 0.0
                    d.ctrl[4:22] = cur_pose
                    d.qpos[12:30] = cur_pose

                if transform_counter >= transform_duration:
                    phase = 0
                    morph_alpha = 0.0
                    in_walking_mode = False
                    chassis_z_curr = 0.240
                    transform_cooldown = 150
                    d.ctrl[4:22] = STOW_POSE
                    d.qpos[12:30] = STOW_POSE
                    print(f"✅ [Step {step:05d}] TRANSFORMATION TO WHEELS COMPLETE! Hooks locked in side pockets. Front/rear wheels engaged.\n", flush=True)

            # -------------------------------------------------------------
            # 6. ANTI-STALL WATCHDOG (PREVENTS WEDGING / SADDLE POINTS)
            # -------------------------------------------------------------
            # Scene-derived A* route around the full swept leg envelope.
            closest_dist_this_step = 999.0
            if phase != 0:
                v_target = omega_target = err_yaw = 0.0
            elif manual_mode:
                if time.time() - last_key_time > .50:
                    manual_v *= .90
                    manual_omega *= .85
                v_target, omega_target = manual_v, manual_omega
            else:
                try:
                    navigation_goal = navigator.steer(curr_pos, active_waypoint)
                    direction = navigation_goal - curr_pos
                    err_yaw = norm_ang(math.atan2(direction[1], direction[0]) - yaw)
                    vmax = .85*(1.-morph_alpha) + .38*morph_alpha
                    # Turn on the spot for large heading changes; slow near corners.
                    heading_factor = max(0., math.cos(err_yaw))**3
                    remaining = float(np.linalg.norm(direction))
                    v_target = min(vmax, math.sqrt(2.*.45*max(0.,remaining-.10))) * heading_factor
                    omega_target = float(1.1*math.tanh(2.1*err_yaw))
                except RuntimeError as error:
                    v_target = omega_target = 0.0
                    if step % 250 == 0:
                        route_failures += 1
                        print(f"[NAVIGATION HOLD] {error}", flush=True)
            # -------------------------------------------------------------
            # 8. TERRAIN CLASSIFICATION & DEDICATED TRANSFORMATION TRIGGERS
            # -------------------------------------------------------------
            in_forest = is_in_bbox(rx, ry, ZONE_BBOX_FOREST)
            in_mud = is_in_bbox(rx, ry, ZONE_BBOX_MUD)
            in_rocks = is_in_bbox(rx, ry, ZONE_BBOX_ROCKY)
            in_sand = is_in_bbox(rx, ry, ZONE_BBOX_SAND)

            if transform_cooldown > 0:
                transform_cooldown -= 1

            active_trav_obs = None
            for tobs in TRAVERSABLE_OBSTACLES:
                d_trav = float(np.linalg.norm(curr_pos - tobs["pos"]))
                # Hysteresis: trigger enter at 1.15m, stay active until 1.85m
                thresh = 1.85 if in_walking_mode else 1.15
                if d_trav < thresh:
                    active_trav_obs = tobs
                    break

            is_rough_terrain = in_forest or in_mud or in_rocks or in_sand or (mission_stage == "circuit" and not is_recharge_divert) or (active_trav_obs is not None)

            # Dedicated Phased Transformation Triggers
            if phase == 0 and not manual_mode and transform_cooldown <= 0:
                if is_rough_terrain and not in_walking_mode:
                    phase = 4  # Start Dedicated Phased Transformation to Legs
                    transform_counter = 0
                    v_smooth = 0.0
                    omega_smooth = 0.0
                    d.ctrl[0:4] = 0.0
                    d.qvel[0:6] = 0.0
                    if active_trav_obs is not None:
                        obs_msg = f"TRAVERSABLE OBSTACLE ({active_trav_obs['label']})"
                    elif in_forest or (mission_stage == "circuit" and target_idx == 0):
                        obs_msg = "ALPINE PINE FOREST & RESEARCH CAMP"
                    elif in_mud:
                        obs_msg = "CHURNED WET MUD PIT & BOG"
                    elif in_rocks:
                        obs_msg = "BROKEN GRANITE QUARRY & CAUSEWAY"
                    else:
                        obs_msg = "GOLDEN DESERT SAND DUNES & RUINS"
                    print(f"\n🐾 [Step {step:05d}] ENTERING ROUGH ROAD: {obs_msg.upper()}!", flush=True)
                    print("   🛑 Hexapod halts cleanly for Dedicated Transformation Sequence (Wheels -> 6 Articulated Legs)...", flush=True)

                elif not is_rough_terrain and in_walking_mode:
                    phase = 5  # Start Dedicated Phased Transformation to Wheels
                    transform_counter = 0
                    v_smooth = 0.0
                    omega_smooth = 0.0
                    d.ctrl[0:4] = 0.0
                    d.qvel[0:6] = 0.0
                    print(f"\n🏎️  [Step {step:05d}] EXITED ROUGH TERRAIN! Smooth ground / arterial highway detected.", flush=True)
                    print("   🛑 Hexapod halts cleanly for Dedicated Transformation Sequence (6 Legs -> Front/Rear Wheels)...", flush=True)

            # Dynamic continuous chassis height target
            chassis_z_target = 0.240 * (1.0 - morph_alpha) + 0.480 * morph_alpha
            chassis_z_curr = 0.92 * chassis_z_curr + 0.08 * chassis_z_target

            # -------------------------------------------------------------
            # 9. STOWED COVER GEOMETRY & COLLISION-FREE TRIPOD GAIT
            # -------------------------------------------------------------
            # Authentic Autodesk Fusion 360 Hexapod:
            # Stowed Pose: All 6 legs folded smoothly alongside CAD chassis (hooks locked in side pockets)
            STOW_POSE = np.array([
                # Left: LF, LM, LR (coxa, femur, tibia)
                 0.00,  1.047, -2.00,  # LF: Tucked along front-left flank, hook locked in top cover pocket
                 0.00,  1.047, -2.00,  # LM: Tucked along mid-left flank, hook locked in top cover pocket
                 0.00,  1.047, -2.00,  # LR: Tucked along rear-left flank, hook locked in top cover pocket
                # Right: RF, RM, RR (coxa, femur, tibia)
                 0.00,  1.047, -2.00,  # RF: Tucked along front-right flank, hook locked in top cover pocket
                 0.00,  1.047, -2.00,  # RM: Tucked along mid-right flank, hook locked in top cover pocket
                 0.00,  1.047, -2.00,  # RR: Tucked along rear-right flank, hook locked in top cover pocket
            ], dtype=np.float32)

            NEUTRAL_STAND_POSE = np.array([
                # Left: LF, LM, LR (coxa, femur, tibia)
                -0.45,  0.20, -1.30,  # LF: Natural forward-outward stance
                 0.00,  0.20, -1.30,  # LM: Natural lateral stance
                 0.45,  0.20, -1.30,  # LR: Natural backward-outward stance
                # Right: RF, RM, RR (coxa, femur, tibia)
                 0.45,  0.20, -1.30,  # RF: Natural forward-outward stance
                 0.00,  0.20, -1.30,  # RM: Natural lateral stance
                -0.45,  0.20, -1.30,  # RR: Natural backward-outward stance
            ], dtype=np.float32)

            if phase in (4, 5):
                gait.reset()
                # Actively articulated by Dedicated Phased Transformation Controller
                pass

            elif phase in (1, 2, 3):
                # Stationary Dwell (Recharging, Scanning, or Base Staging)
                if in_walking_mode:
                    chassis_z_curr = 0.480
                    d.ctrl[4:22] = gait.targets(curr_pos, yaw, float(d.qpos[2]), 0., 0.)
                else:
                    chassis_z_curr = 0.240
                    d.ctrl[4:22] = STOW_POSE
                    d.qvel[11:29] = 0.0
                    d.qpos[12:30] = STOW_POSE

            elif not in_walking_mode:
                gait.reset()
                # 100% PURE WHEELED CRUISE: Legs locked completely motionless alongside chassis
                chassis_z_curr = 0.240
                d.ctrl[4:22] = STOW_POSE
                d.qvel[11:29] = 0.0
                d.qpos[12:30] = STOW_POSE
                walk_step_count = 0

            else:
                # Ground-referenced feet: stance feet stay planted while swings
                # follow a zero-end-velocity trajectory with 13cm clearance.
                chassis_z_curr = .480
                d.ctrl[4:22] = gait.targets(curr_pos, yaw, float(d.qpos[2]), v_smooth, omega_smooth)

            # -------------------------------------------------------------
            # 10. WHEEL MOTOR ENGAGEMENT & SMOOTH CHASSIS DYNAMICS
            # -------------------------------------------------------------
            if transforming_this_frame:
                safe_pose = clear_transform_feet(d.qpos[12:30], float(d.qpos[2]))
                d.qpos[12:30] = safe_pose
                d.ctrl[4:22] = safe_pose
                d.qvel[11:29] = 0.0
            if phase == 0:
                max_dv = 0.010  # acceleration clamp (0.625 m/s^2) for silky smooth transitions
                v_smooth = float(np.clip(v_target, v_smooth - max_dv, v_smooth + max_dv))
                max_domega = 0.030  # angular accel clamp (1.875 rad/s^2) prevents abrupt steering snaps
                omega_smooth = float(np.clip(omega_target, omega_smooth - max_domega, omega_smooth + max_domega))
            else:
                v_smooth = 0.0
                omega_smooth = 0.0

            # Wheel motor drive: active when wheels are on ground (not in_walking_mode and phase == 0)
            if not in_walking_mode and phase == 0:
                R = 0.090  # Wheel radius (m)
                B = 0.44   # Track width (m) (front & rear wheels at y = +-0.22m)
                omega_L = (v_smooth - omega_smooth * B / 2.0) / R
                omega_R = (v_smooth + omega_smooth * B / 2.0) / R

                # Actuate front & rear wheel motors
                d.ctrl[0] = omega_L   # Front Left
                d.ctrl[1] = omega_R   # Front Right
                d.ctrl[2] = omega_L   # Rear Left
                d.ctrl[3] = omega_R   # Rear Right

                # Synchronize wheel joint velocities
                d.qvel[wheel_dofs] = [omega_L, omega_R, omega_L, omega_R]
            else:
                d.ctrl[0:4] = 0.0
                d.qvel[wheel_dofs] = 0.0

            safe_v, safe_omega = navigator.limit_motion(curr_pos, yaw, v_smooth, omega_smooth)
            if abs(safe_v-v_smooth) > 1e-6:
                safety_stops += 1
                navigator.goal_key = None
            v_smooth, omega_smooth = safe_v, safe_omega
            d.qvel[0] = v_smooth * math.cos(yaw)
            d.qvel[1] = v_smooth * math.sin(yaw)
            d.qvel[5] = omega_smooth

            # Active level attitude and height stabilization RUNS IN ALL PHASES
            d.qvel[2] = float(np.clip(8.0 * (chassis_z_curr - d.qpos[2]), -1.5, 1.5))
            d.qvel[3] = float(np.clip(-10.0 * roll, -2.5, 2.5))
            d.qvel[4] = float(np.clip(-10.0 * pitch, -2.5, 2.5))

            # Keep every physical substep observable; never ignore leg contacts.
            for _ in range(4):
                mujoco.mj_step(m, d)
                for contact in d.contact:
                    pair = (int(contact.geom1), int(contact.geom2))
                    if ((pair[0] in navigator.robot_geom_set and pair[1] in navigator.obstacle_geom_set)
                        or (pair[1] in navigator.robot_geom_set and pair[0] in navigator.obstacle_geom_set)):
                        min_surface_clearance = min(min_surface_clearance, float(contact.dist))
                        if contact.dist <= .001:
                            obstacle_contact_substeps += 1
                        if contact.dist < -.001:
                            total_collisions += 1

            if phase == 0 and in_walking_mode:
                actual_roll, actual_pitch, _ = get_roll_pitch_yaw(d)
                max_body_tilt = max(max_body_tilt, abs(actual_roll), abs(actual_pitch))
                minimum_foot_bottom = min(minimum_foot_bottom, min(d.geom_xpos[m.geom('foot_'+leg).id,2]-.045 for leg in ('LF','LM','LR','RF','RM','RR')))

            # Camera View Management: Native MuJoCo tracking & zero-override free / overview cam
            # Presets 0 & 3 (Tracking): ensure native body tracking without overriding user orbit/zoom angles!
            # Presets 1 & 2 (Overview & Free): do not touch viewer.cam in the loop (user can pan/zoom anywhere across 72m arena!)
            if cam_preset in (0, 3):
                if viewer.cam.type != mujoco.mjtCamera.mjCAMERA_TRACKING:
                    viewer.cam.type = mujoco.mjtCamera.mjCAMERA_TRACKING
                    viewer.cam.trackbodyid = m.body('robot').id

            viewer.sync()

            # Periodic Watchdog Telemetry Summary (every 500 steps)
            if step % 500 == 0:
                elapsed_mins = (time.time() - start_time) / 60.0
                loco_str = "6-LEGGED TRIPOD IK" if in_walking_mode else "4-WHEEL DIRECT DRIVE"
                fill_count = int(np.clip(battery / 20.0, 0, 5))
                gauge_str = "🟩" * fill_count + "⬜" * (5 - fill_count)
                status_str = "RECHARGING" if phase == 1 else ("SCANNING" if phase == 2 else ("STAGING" if phase == 3 else f"CRUISING ({mission_stage.upper()})"))
                lidar_str = "ACTIVE (7-BEAM)" if is_active_scanning else "STANDBY"
                print(f"📊 [TELEMETRY Step {step:06d} | Lap {lap_count} | {elapsed_mins:.1f}m] Pos: ({rx:.1f}, {ry:.1f}) | Target: {active_target['name']} | Status: {status_str} | LiDAR: {lidar_str} | Mode: {loco_str} | Bat: {battery:.1f}% [{gauge_str}] | Route replans: {navigator.replans} | Safety holds: {safety_stops}", flush=True)

            elapsed = time.time() - step_start
            if not args.headless:
                time.sleep(max(0.0, 0.016 - elapsed))

        report = dict(steps=step, simulation_seconds=float(d.time), battery=battery,
                      position=d.qpos[:3].tolist(), phase=phase, target=target_idx+1,
                      stage=mission_stage, corridor_index=corridor_idx,
                      collision_substeps=total_collisions, obstacle_contact_substeps=obstacle_contact_substeps,
                      max_walking_tilt_degrees=math.degrees(max_body_tilt), minimum_foot_bottom=minimum_foot_bottom,
                      safety_stops=safety_stops,
                      route_failures=route_failures, charge_completed=charge_completed,
                      visited_places=sorted(visited_places), replans=navigator.replans,
                      finite_state=bool(np.isfinite(d.qpos).all() and np.isfinite(d.qvel).all()),
                      max_solver_warning=int(sum(w.number for w in d.warning)))
        if args.report:
            Path(args.report).write_text(json.dumps(report,indent=2))
        if getattr(args,'snapshot',None):
            from PIL import Image
            camera = mujoco.MjvCamera()
            camera.lookat[:] = d.qpos[:3]+[0,0,.3]
            camera.distance, camera.elevation, camera.azimuth = 5., -25., 130.
            renderer = mujoco.Renderer(m,720,1000)
            renderer.update_scene(d,camera=camera)
            Image.fromarray(renderer.render()).save(args.snapshot)
            renderer.close()
        print(json.dumps(report,indent=2),flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--headless',action='store_true')
    parser.add_argument('--steps',type=int,default=40000)
    parser.add_argument('--battery-test-step',type=int,default=0)
    parser.add_argument('--dispatch',type=int,choices=range(5),default=1)
    parser.add_argument('--report')
    parser.add_argument('--snapshot')
    run_mission(parser.parse_args())
