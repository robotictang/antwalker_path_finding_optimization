#!/usr/bin/env python3
"""
Enhanced Multi-Place Scene XML Generator for Autodesk Fusion 360 CAD Hexapod
=============================================================================
Features:
- Authentic CAD Model Geometry:
  * base_link.stl, coxa_link.stl, femur_link.stl, tibia_link.stl, rs04_actuator.stl
  * Colors matching hexapod.urdf: chassis_grey, accent_orange, link_grey
  * RS04 brushless motor actuators mounted at all 18 joints
  * Solid physics collision hulls (contype=2, conaffinity=1 vs contype=1, conaffinity=7)
- Form-Fitted Top Cover with Dual Longitudinal Side Pockets
- Leg Transformation Hooks (femurs dock in side pockets during wheeled mode)
- Underbelly Ventral Sensor Bay with 7-beam cyan LiDAR fan
- Massively Enriched 72m x 72m Proving Ground (ZERO Empty Space):
  * Paved asphalt arterial highways with double yellow center lines and white edge lines
  * 4 distinct textured biome ground zones (Forest Moss, Granite Slabs, Wet Mud, Desert Dunes)
  * 50+ perimeter mountain crags, canyon buttresses, alpine spires, security floodlight towers
  * Place 1: 165+ pine trees, research wall tent, watchtower, cabin, campfire, timber ricks, weather mast, fences
  * Place 2: Mining excavator, ore hauler dump truck, derrick crane, 12m conveyor, site office, 32 rock slabs, granite boulders
  * Place 3: 3 reflective water ponds, extensive boardwalk network, 2 stilt huts, lily pads, cattails, buoy, rowboat
  * Place 4: 14 classical sandstone columns, monumental archway, hieroglyphic obelisks, urns, cacti, dig site
  * Small Path Obstacles: Orange traffic cones, roadside rocks, road barriers, stumps
  * Base Depot: 16x12m apron, helipad marking, shipping containers, generator trailer, telemetry mast
  * Charging Plaza: 14x18m concrete plaza, 4.5x4.5m induction pad, 4.2m solar canopy, 12-bay battery wall
"""

import math
import numpy as np
from multi_place_config import (
    DEST_BASE,
    DEST_PLACE_1,
    DEST_PLACE_2,
    DEST_PLACE_3,
    DEST_PLACE_4,
    DEST_KIOSK_PAD,
    DEST_KIOSK_ENTRY,
    DEST_KIOSK,
    TRAVERSABLE_OBSTACLES,
    SITE_STRUCTURE_OBSTACLES,
    SMALL_PATH_OBSTACLES,
)


def generate_place1_pine_trees():
    np.random.seed(42)
    models = ["pine_tall", "pine_mid", "pine_dense", "pine_small"]
    trees = []

    # Dense forest zone [-26, -11] x [8, 25]
    for _ in range(165):
        rx = float(np.random.uniform(-26.0, -10.5))
        ry = float(np.random.uniform(8.5, 25.5))
        p = np.array([rx, ry])

        # Clear transit highways
        if abs(rx - (-10.0)) < 3.0 or abs(ry - 16.0) < 3.2:
            continue
        # Clear camp center stations
        if np.linalg.norm(p - np.array([-18.0, 13.0])) < 3.5:
            continue
        if np.linalg.norm(p - np.array([-21.0, 16.0])) < 3.5:
            continue
        if np.linalg.norm(p - np.array([-18.0, 20.0])) < 3.5:
            continue
        if np.linalg.norm(p - np.array([-14.5, 16.5])) < 3.5:
            continue
        # Clear major camp buildings
        if np.linalg.norm(p - np.array([-24.0, 16.0])) < 3.2:
            continue
        if np.linalg.norm(p - np.array([-26.0, 22.0])) < 3.5:
            continue
        if np.linalg.norm(p - np.array([-25.0, 13.0])) < 3.5:
            continue

        model = str(np.random.choice(models))
        scale = float(np.random.uniform(0.70, 1.45))
        trunk_h = float(np.random.uniform(1.4, 2.8) * scale)
        yaw = float(np.random.uniform(0, 2 * np.pi))
        tilt_x = float(np.random.uniform(-0.04, 0.04))
        tilt_y = float(np.random.uniform(-0.04, 0.04))
        trees.append({
            "pos": [rx, ry],
            "model": model,
            "scale": scale,
            "trunk_h": trunk_h,
            "euler": [tilt_x, tilt_y, yaw]
        })

    return trees


def generate_place2_rock_slabs():
    np.random.seed(137)
    slabs = []
    for _ in range(32):
        rx = float(np.random.uniform(12.5, 25.5))
        ry = float(np.random.uniform(9.5, 23.5))
        p = np.array([rx, ry])

        # Clear highways
        if abs(rx - 10.0) < 3.5 or abs(ry - 16.0) < 3.0:
            continue
        # Clear quarry stations
        if np.linalg.norm(p - np.array([18.0, 13.0])) < 3.0:
            continue
        if np.linalg.norm(p - np.array([14.5, 16.5])) < 3.0:
            continue
        if np.linalg.norm(p - np.array([18.0, 20.0])) < 3.0:
            continue
        if np.linalg.norm(p - np.array([21.5, 16.0])) < 3.0:
            continue
        # Clear heavy machinery
        if np.linalg.norm(p - np.array([15.0, 21.0])) < 3.5:
            continue
        if np.linalg.norm(p - np.array([20.5, 22.0])) < 3.5:
            continue
        if np.linalg.norm(p - np.array([23.0, 17.5])) < 3.5:
            continue

        sx = float(np.random.uniform(0.50, 1.10))
        sy = float(np.random.uniform(0.40, 0.90))
        sz = float(np.random.uniform(0.015, 0.040))
        yaw = float(np.random.uniform(0, 2 * np.pi))
        tilt = float(np.random.uniform(-0.06, 0.06))
        slabs.append({"pos": [rx, ry, sz], "size": [sx, sy, sz], "euler": [tilt, tilt, yaw]})

    return slabs


def generate_enhanced_robot_xml():
    from strict_asset import build_robot_xml
    return build_robot_xml()


def generate_spacious_charging_plaza_xml():
    """
    Generates the Honda e:TECHNOLOGY Autonomous Battery Swap Locker Station
    Matching the User Reference Image (media_1792546549217_50207a12.png):
    - Monolithic tall cabinet (open-air, NO canopy roof, NO 4 petrol pillars!)
    - Dark slate body chassis with adjustable leveling foot pins
    - White front fascia frame with elegant forward-curved top cowl
    - "Honda e:TECHNOLOGY" cyan branding stripe on the top cowl
    - Upper horizontal louvered grille with interactive digital telemetry LCD touchscreen on right
    - 3-column x 4-row matrix of 12 swappable battery bays:
        * Angled dark recessed pockets
        * Brilliant neon blue LED halo illumination borders
        * Inserted Honda Mobile Power Pack batteries with vivid electric blue top handles & "e:" emblem
        * 2 empty receiver bays on bottom tier ready for hot-swap
    - 2 Standalone Reserve Honda Mobile Power Pack battery units sitting on the staging pad beside the kiosk
    - Induction charging platform with glowing emerald green docking target ring
    - Open-air concrete staging apron with yellow chevron approach markings
    """
    cols = [-0.38, 0.00, 0.38]
    rows = [1.54, 1.22, 0.90, 0.58]

    bays_xml = ""
    for r_idx, rz in enumerate(rows):
        for c_idx, cx in enumerate(cols):
            slot_num = r_idx * 3 + c_idx + 1
            # Recessed pocket chamber inside cabinet (y = -0.380)
            bays_xml += f"""      <geom name="bay_pocket_{slot_num}" type="box" size="0.140 0.035 0.115" pos="{cx:.3f} -0.380 {rz:.3f}" material="honda_bay_pocket" contype="0" conaffinity="0"/>
      <geom name="bay_bezel_{slot_num}" type="box" size="0.165 0.002 0.135" pos="{cx:.3f} -0.418 {rz:.3f}" material="honda_cabinet_dark" contype="0" conaffinity="0"/>
      <geom name="bay_halo_{slot_num}"  type="box" size="0.155 0.002 0.125" pos="{cx:.3f} -0.421 {rz:.3f}" material="honda_slot_blue_led" contype="0" conaffinity="0"/>\n"""

            if r_idx < 3 or c_idx == 0:
                # Populated with Honda Mobile Power Pack battery!
                bays_xml += f"""      <geom name="bat_body_{slot_num}" type="box" size="0.115 0.035 0.085" pos="{cx:.3f} -0.435 {rz-0.015:.3f}" material="honda_battery_body" contype="0" conaffinity="0"/>
      <geom name="bat_logo_{slot_num}" type="box" size="0.035 0.002 0.028" pos="{cx:.3f} -0.472 {rz-0.035:.3f}" material="honda_brand_teal" contype="0" conaffinity="0"/>
      <geom name="bat_handle_{slot_num}" type="capsule" size="0.012" fromto="{cx-0.065:.3f} -0.445 {rz+0.055:.3f} {cx+0.065:.3f} -0.445 {rz+0.055:.3f}" material="honda_cabinet_dark" contype="0" conaffinity="0"/>
      <geom name="bat_grip_{slot_num}" type="capsule" size="0.015" fromto="{cx-0.038:.3f} -0.445 {rz+0.055:.3f} {cx+0.038:.3f} -0.445 {rz+0.055:.3f}" material="honda_handle_blue" contype="0" conaffinity="0"/>\n"""
            else:
                # Empty swap receiver bays ready for robot hot-swap!
                bays_xml += f"""      <geom name="dock_pin_{slot_num}_1" type="cylinder" size="0.008 0.015" pos="{cx-0.04:.3f} -0.345 {rz:.3f}" euler="1.5708 0 0" material="field_station_metal" contype="0" conaffinity="0"/>
      <geom name="dock_pin_{slot_num}_2" type="cylinder" size="0.008 0.015" pos="{cx+0.04:.3f} -0.345 {rz:.3f}" euler="1.5708 0 0" material="field_station_metal" contype="0" conaffinity="0"/>\n"""

    xml = f"""
    <!-- ================= HONDA e:TECHNOLOGY BATTERY SWAP STATION (MATCHING USER REFERENCE IMAGE) ================= -->
    <!-- Open-Air Concrete Staging Apron (NO PETROL CANOPY ROOF, NO 4 PYLONS!) -->
    <geom name="plaza_foundation" type="box" size="5.50 6.50 0.012" pos="0.0 4.0 0.012" material="concrete_pad_mat" contype="0" conaffinity="0"/>

    <!-- Clear Central Guidance Runway Chevrons leading to Docking Pad -->
    <geom name="plaza_apron_chevron_1" type="box" size="1.20 0.15 0.002" pos="0.0 -3.0 0.026" material="hazard_yellow_mat" contype="0" conaffinity="0"/>
    <geom name="plaza_apron_chevron_2" type="box" size="1.20 0.15 0.002" pos="0.0 -1.5 0.026" material="hazard_yellow_mat" contype="0" conaffinity="0"/>
    <geom name="plaza_apron_chevron_3" type="box" size="1.20 0.15 0.002" pos="0.0  0.0 0.026" material="hazard_yellow_mat" contype="0" conaffinity="0"/>

    <!-- Perimeter Boundary Curbs with Yellow Hazard Markings -->
    <geom name="plaza_curb_left"  type="box" size="0.20 6.2 0.08" pos="-5.30 4.0 0.08" material="kiosk_pedestal_mat" contype="0" conaffinity="0"/>
    <geom name="plaza_curb_right" type="box" size="0.20 6.2 0.08" pos=" 5.30 4.0 0.08" material="kiosk_pedestal_mat" contype="0" conaffinity="0"/>
    <geom name="plaza_curb_back"  type="box" size="5.40 0.20 0.08" pos=" 0.00 10.2 0.08" material="kiosk_pedestal_mat" contype="0" conaffinity="0"/>

    <!-- Dedicated Central Rapid-Induction Docking Pad [0.0, 1.2] -->
    <body name="kiosk_docking_pad" pos="{DEST_KIOSK_PAD[0]:.3f} {DEST_KIOSK_PAD[1]:.3f} 0.020">
      <geom name="dock_plate" type="cylinder" size="2.25 0.015" pos="0 0 0.015" material="concrete_pad_mat" contype="0" conaffinity="0"/>
      <!-- Glowing High-Output Emerald Green Guidance & Alignment Rings -->
      <geom name="dock_ring_outer" type="cylinder" size="2.15 0.003" pos="0 0 0.032" material="kiosk_led_green" contype="0" conaffinity="0"/>
      <geom name="dock_ring_mid"   type="cylinder" size="1.65 0.004" pos="0 0 0.034" material="kiosk_pedestal_mat" contype="0" conaffinity="0"/>
      <geom name="dock_ring_inner" type="cylinder" size="1.45 0.005" pos="0 0 0.036" material="kiosk_led_green" contype="0" conaffinity="0"/>
      <geom name="dock_center_target" type="cylinder" size="0.55 0.006" pos="0 0 0.038" material="scan_core_mat" contype="0" conaffinity="0"/>
      <!-- Alignment Target Crosshairs -->
      <geom type="box" size="2.00 0.04 0.004" pos="0 0 0.035" material="hazard_yellow_mat" contype="0" conaffinity="0"/>
      <geom type="box" size="0.04 2.00 0.004" pos="0 0 0.035" material="hazard_yellow_mat" contype="0" conaffinity="0"/>
    </body>

    <!-- Protective Safety Bollards Flanking the Station Apron (Safely at x = +/-3.5m) -->
    <body name="kiosk_bollard_l" pos="-3.5 2.0 0">
      <geom type="cylinder" size="0.14 0.45" pos="0 0 0.45" material="field_station_metal" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.145 0.06" pos="0 0 0.70" material="hazard_yellow_mat" contype="0" conaffinity="0"/>
    </body>
    <body name="kiosk_bollard_r" pos="3.5 2.0 0">
      <geom type="cylinder" size="0.14 0.45" pos="0 0 0.45" material="field_station_metal" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.145 0.06" pos="0 0 0.70" material="hazard_yellow_mat" contype="0" conaffinity="0"/>
    </body>

    <!-- ================= HONDA e:SWAP MONOLITHIC KIOSK TOWER (pos: 0.0, 8.2) ================= -->
    <body name="kiosk_tower" pos="{DEST_KIOSK[0]:.3f} {DEST_KIOSK[1]:.3f} 0">
      <!-- Dark Slate Base Pedestal with 4 Corner Leveling Feet -->
      <geom name="honda_base_pedestal" type="box" size="0.82 0.44 0.12" pos="0 0 0.12" material="honda_cabinet_dark" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.025 0.04" pos="-0.75 -0.38 0.04" material="field_station_metal" contype="0" conaffinity="0"/>
      <geom type="cylinder" size="0.025 0.04" pos=" 0.75 -0.38 0.04" material="field_station_metal" contype="0" conaffinity="0"/>
      <geom type="cylinder" size="0.025 0.04" pos="-0.75  0.38 0.04" material="field_station_metal" contype="0" conaffinity="0"/>
      <geom type="cylinder" size="0.025 0.04" pos=" 0.75  0.38 0.04" material="field_station_metal" contype="0" conaffinity="0"/>

      <!-- Main Dark Slate Cabinet Housing -->
      <geom name="honda_main_cabinet" type="box" size="0.78 0.40 1.05" pos="0 0 1.25" material="honda_cabinet_dark" contype="1" conaffinity="7"/>

      <!-- White Glossy Front Fascia Frame (y = -0.408) -->
      <geom name="honda_front_frame" type="box" size="0.78 0.008 0.96" pos="0 -0.408 1.15" material="honda_white_fascia" contype="0" conaffinity="0"/>

      <!-- Upper Forward-Curved Top Cowl / Hood (Distinctive Honda Curved Profile) -->
      <geom name="honda_cowl_box" type="box" size="0.78 0.38 0.08" pos="0 0 2.36" material="honda_white_fascia" contype="1" conaffinity="7"/>
      <geom name="honda_cowl_curve" type="cylinder" size="0.10 0.77" pos="0 -0.36 2.34" euler="0 1.5708 0" material="honda_white_fascia" contype="0" conaffinity="0"/>
      <geom name="honda_cowl_hood" type="box" size="0.77 0.03 0.10" pos="0 -0.410 2.24" material="honda_white_fascia" contype="0" conaffinity="0"/>

      <!-- "Honda e:TECHNOLOGY" Cyan Brand Emblem Stripe atop Cowl -->
      <geom name="honda_brand_emblem" type="box" size="0.26 0.004 0.016" pos="-0.26 -0.432 2.28" material="honda_brand_teal" contype="0" conaffinity="0"/>

      <!-- Upper Louvered Horizontal Ventilation Grille (y = -0.418) -->
      <geom name="honda_grille_backing" type="box" size="0.72 0.003 0.16" pos="0 -0.418 1.94" material="honda_grille_gray" contype="0" conaffinity="0"/>
      <geom type="box" size="0.71 0.003 0.010" pos="0 -0.424 2.05" material="honda_cabinet_dark" contype="0" conaffinity="0"/>
      <geom type="box" size="0.71 0.003 0.010" pos="0 -0.424 1.98" material="honda_cabinet_dark" contype="0" conaffinity="0"/>
      <geom type="box" size="0.71 0.003 0.010" pos="0 -0.424 1.91" material="honda_cabinet_dark" contype="0" conaffinity="0"/>
      <geom type="box" size="0.71 0.003 0.010" pos="0 -0.424 1.84" material="honda_cabinet_dark" contype="0" conaffinity="0"/>

      <!-- Interactive Digital Telemetry LCD Touchscreen on Upper Right -->
      <geom name="honda_screen_bezel" type="box" size="0.16 0.004 0.12" pos="0.28 -0.424 1.94" material="honda_cabinet_dark" contype="0" conaffinity="0"/>
      <geom name="honda_screen_lcd"   type="box" size="0.14 0.002 0.10" pos="0.28 -0.429 1.94" material="kiosk_screen_mat" contype="0" conaffinity="0"/>

      <!-- 12 Autonomous Battery Swap Bays (3 Columns x 4 Rows) with Neon Blue LED Halos -->
{bays_xml}
    </body>

    <!-- ================= STANDALONE RESERVE HONDA MOBILE POWER PACK BATTERIES ================= -->
    <!-- Two reserve battery packs sitting side by side on staging pad (Matching Reference Photo) -->
    <body name="reserve_pack_1" pos="-1.05 7.60 0.0">
      <geom name="res_bat_1_body" type="box" size="0.085 0.085 0.17" pos="0 0 0.17" material="honda_battery_body" contype="1" conaffinity="7"/>
      <geom name="res_bat_1_handle" type="capsule" size="0.012" fromto="-0.055 0 0.36 0.055 0 0.36" material="honda_cabinet_dark" contype="0" conaffinity="0"/>
      <geom name="res_bat_1_grip" type="capsule" size="0.015" fromto="-0.035 0 0.36 0.035 0 0.36" material="honda_handle_blue" contype="0" conaffinity="0"/>
      <geom name="res_bat_1_logo" type="box" size="0.035 0.002 0.030" pos="0 -0.087 0.20" material="honda_brand_teal" contype="0" conaffinity="0"/>
    </body>

    <body name="reserve_pack_2" pos="-0.80 7.60 0.0">
      <geom name="res_bat_2_body" type="box" size="0.085 0.085 0.17" pos="0 0 0.17" material="honda_battery_body" contype="1" conaffinity="7"/>
      <geom name="res_bat_2_handle" type="capsule" size="0.012" fromto="-0.055 0 0.36 0.055 0 0.36" material="honda_cabinet_dark" contype="0" conaffinity="0"/>
      <geom name="res_bat_2_grip" type="capsule" size="0.015" fromto="-0.035 0 0.36 0.035 0 0.36" material="honda_handle_blue" contype="0" conaffinity="0"/>
      <geom name="res_bat_2_logo" type="box" size="0.035 0.002 0.030" pos="0 -0.087 0.20" material="honda_brand_teal" contype="0" conaffinity="0"/>
    </body>

    <!-- High-Voltage Grid Inverter Cabinet (Safely on West Flank at x = -4.5m) -->
    <body name="plaza_transformer" pos="-4.50 7.80 0.60">
      <geom type="box" size="0.60 0.45 0.60" material="utility_gray_mat" contype="1" conaffinity="7"/>
      <geom type="box" size="0.25 0.02 0.35" pos="0 -0.46 0" material="hazard_yellow_mat" contype="0" conaffinity="0"/>
      <geom type="cylinder" size="0.02 0.20" pos="0.20 0 0.70" material="field_station_metal" contype="0" conaffinity="0"/>
    </body>
"""
    return xml


def build_full_scene_xml(output_path="hybrid_hexapod_multi_place.xml"):
    """Compiles the complete 72m x 72m scene with all rich elements, authentic CAD robot, and collision physics."""
    trees = generate_place1_pine_trees()
    slabs = generate_place2_rock_slabs()

    xml = f"""<mujoco model="open_world_hexapod_expedition">
  <compiler angle="radian" coordinate="local" autolimits="true"/>

  <option timestep="0.004" iterations="50" solver="Newton" integrator="implicitfast" gravity="0 0 -9.81">
    <flag contact="enable" frictionloss="enable"/>
  </option>

  <!-- Atmospheric Outdoor Lighting & Realistic Skybox -->
  <visual>
    <global offwidth="1920" offheight="1080"/>
    <quality shadowsize="4096"/>
    <map stiffness="100" shadowscale="0.6"/>
    <headlight ambient="0.48 0.46 0.42" diffuse="0.55 0.53 0.50" specular="0.22 0.22 0.20"/>
  </visual>

  <asset>
    <!-- Panoramic Gradient Skybox -->
    <texture name="skybox_tex" type="skybox" builtin="gradient" rgb1="0.45 0.65 0.88" rgb2="0.82 0.90 0.96" width="1024" height="1024"/>

    <!-- 3D Conifer, Boulder & Fallen Log Meshes -->
    <mesh name="pine_tall_mesh" file="models/pine_tall.obj"/>
    <mesh name="pine_mid_mesh" file="models/pine_mid.obj"/>
    <mesh name="pine_dense_mesh" file="models/pine_dense.obj"/>
    <mesh name="pine_small_mesh" file="models/pine_small.obj"/>
    <mesh name="rock1_mesh" file="models/granite_rock1.obj"/>
    <mesh name="small_rock_mesh" file="models/granite_rock1.obj" scale="0.40 0.40 0.32"/>
    <mesh name="rock2_mesh" file="models/granite_rock2.obj"/>
    <mesh name="log_mesh" file="models/fallen_log.obj"/>

    <!-- Authentic Autodesk Fusion 360 Hexapod CAD Meshes + High-Fidelity Ant Carapace Top Cover Mesh -->
    <mesh name="mesh_base_link" file="meshes/base_link.stl" scale="0.001 0.001 0.001"/>
    <mesh name="mesh_top_cover" file="meshes/top_cover.stl" scale="0.001 0.001 0.001"/>
    <mesh name="mesh_coxa_link" file="meshes/coxa_link.stl" scale="0.001 0.001 0.001"/>
    <mesh name="mesh_femur_link" file="meshes/femur_link.stl" scale="0.001 0.001 0.001"/>
    <mesh name="mesh_tibia_link" file="meshes/tibia_link.stl" scale="0.001 0.001 0.001"/>
    <mesh name="mesh_rs04_actuator" file="meshes/rs04_actuator.stl" scale="0.001 0.001 0.001"/>

    <!-- Authentic CAD Materials Matching hexapod.urdf -->
    <material name="chassis_cad_mat" rgba="0.25 0.25 0.28 1.0" specular="0.45" roughness="0.55"/>
    <material name="carapace_carbon" rgba="0.13 0.14 0.16 1.0" specular="0.85" roughness="0.18"/>
    <material name="coxa_cad_mat"    rgba="0.85 0.45 0.10 1.0" specular="0.65" roughness="0.30"/>
    <material name="leg_cad_mat"     rgba="0.30 0.30 0.32 1.0" specular="0.55" roughness="0.40"/>
    <material name="rs04_cad_mat"    rgba="0.18 0.18 0.20 1.0" specular="0.70" roughness="0.25"/>

    <!-- High-Resolution Seamless Unified Biome Terrain Textures -->
    <texture name="earth_ground_tex" type="2d" file="textures/realistic_terrain_earth.png"/>
    <texture name="rock_granite_tex" type="2d" file="textures/realistic_rock_granite.png"/>
    <texture name="bark_wood_tex" type="2d" file="textures/realistic_tree_bark.png"/>
    <texture name="pine_needles_tex" type="2d" file="textures/pine_needles.png"/>
    <texture name="concrete_pad_tex" type="2d" file="textures/concrete_dock_pad.png"/>
    <texture name="kiosk_screen_tex" type="2d" file="textures/kiosk_screen.png"/>
    <texture name="kiosk_lockers_tex" type="2d" file="textures/kiosk_lockers.png"/>
    <texture name="wet_mud_tex" type="2d" file="textures/realistic_wet_mud.png"/>
    <texture name="sand_gravel_tex" type="2d" file="textures/realistic_sand_gravel.png"/>
    <texture name="forest_moss_tex" type="2d" file="textures/realistic_forest_moss_soil.png"/>
    <texture name="dirt_trail_tex" type="2d" file="textures/forest_dirt_path.png"/>

    <!-- Continuous Unified Biome Terrain Material (1:1 mapping over 72m x 72m world) -->
    <material name="world_base_mat" texture="earth_ground_tex" texrepeat="1 1" rgba="0.95 0.95 0.95 1.0" reflectance="0.04" roughness="0.95"/>

    <!-- Distinct Biome Ground Materials -->
    <material name="forest_ground_mat" texture="forest_moss_tex" texrepeat="3 3" rgba="0.88 0.95 0.85 1.0" roughness="0.95" reflectance="0.04"/>
    <material name="dirt_trail_mat" texture="dirt_trail_tex" texrepeat="2 4" rgba="0.85 0.75 0.65 1.0" roughness="0.90"/>
    <material name="quarry_ground_mat" texture="rock_granite_tex" texrepeat="4 4" rgba="0.75 0.75 0.78 1.0" roughness="0.85" reflectance="0.15"/>
    <material name="mud_marsh_ground_mat" texture="wet_mud_tex" texrepeat="3 3" rgba="0.55 0.45 0.38 1.0" roughness="0.92" reflectance="0.12"/>
    <material name="desert_sand_ground_mat" texture="sand_gravel_tex" texrepeat="3 3" rgba="0.95 0.82 0.58 1.0" roughness="0.90" reflectance="0.10"/>

    <!-- Arterial Road & Highway Materials -->
    <material name="asphalt_highway_mat" texture="earth_ground_tex" texrepeat="2 8" rgba="0.25 0.25 0.28 1.0" reflectance="0.10" roughness="0.88"/>
    <material name="road_stripe_yellow" rgba="0.98 0.82 0.12 1.0" emission="0.45"/>
    <material name="road_stripe_white" rgba="0.95 0.95 0.95 1.0" emission="0.40"/>
    <material name="traffic_cone_orange" rgba="0.98 0.42 0.05 1.0" emission="0.40"/>
    <material name="cone_white_stripe" rgba="0.98 0.98 0.98 1.0" emission="0.50"/>

    <!-- Biome Materials for 3D Elements -->
    <material name="pine_trunk_mat" texture="bark_wood_tex" texrepeat="1 6" rgba="0.52 0.38 0.26 1.0" reflectance="0.05" roughness="0.95"/>
    <material name="pine_foliage_mat" texture="pine_needles_tex" texrepeat="3 3" rgba="0.65 0.85 0.65 1.0" roughness="0.90" reflectance="0.05"/>
    <material name="bush_foliage_mat" rgba="0.28 0.52 0.22 1.0" roughness="0.90"/>
    <material name="broken_slab_mat" texture="rock_granite_tex" texrepeat="1 1" rgba="0.65 0.65 0.68 1.0" reflectance="0.22" roughness="0.78"/>
    <material name="gravel_mat" texture="rock_granite_tex" texrepeat="4 4" rgba="0.58 0.56 0.54 1.0" roughness="0.92"/>
    <material name="marsh_water_mat" rgba="0.08 0.18 0.16 0.95" specular="0.98" emission="0.10" reflectance="0.95" roughness="0.02"/>
    <material name="mud_berm_mat" texture="wet_mud_tex" texrepeat="2 2" rgba="0.42 0.32 0.24 1.0" roughness="0.95" reflectance="0.08"/>
    <material name="dune_sand_mat" texture="sand_gravel_tex" texrepeat="2 2" rgba="0.88 0.72 0.48 1.0" reflectance="0.10" roughness="0.92"/>
    <material name="sandstone_mat" texture="sand_gravel_tex" texrepeat="1 2" rgba="0.82 0.60 0.42 1.0" reflectance="0.12" roughness="0.88"/>
    <material name="terracotta_mat" rgba="0.78 0.44 0.28 1.0" roughness="0.88"/>
    <material name="granite_rock_mat" texture="rock_granite_tex" texrepeat="2 2" reflectance="0.14" roughness="0.86"/>
    <material name="fallen_log_mat" texture="bark_wood_tex" texrepeat="1 3" reflectance="0.06" roughness="0.92"/>
    <material name="stump_bark_mat" texture="bark_wood_tex" texrepeat="1 2" reflectance="0.06" roughness="0.92"/>
    <material name="stump_heartwood" rgba="0.44 0.30 0.16 1.0"/>

    <!-- Research Camp & Expedition Materials -->
    <material name="tent_canvas_mat" rgba="0.85 0.80 0.68 1.0" reflectance="0.15" roughness="0.85"/>
    <material name="tent_fly_mat" rgba="0.22 0.38 0.26 1.0" reflectance="0.25" roughness="0.75"/>
    <material name="camp_wood_mat" texture="bark_wood_tex" rgba="0.45 0.35 0.25 1.0" roughness="0.85"/>
    <material name="crate_metal_mat" rgba="0.45 0.48 0.52 1.0" reflectance="0.30"/>
    <material name="field_station_metal" rgba="0.78 0.80 0.82 1.0" reflectance="0.35"/>
    <material name="solar_cell_mat" rgba="0.12 0.16 0.28 1.0" reflectance="0.55" specular="0.9"/>
    <material name="survey_flag_orange" rgba="0.95 0.42 0.10 1.0"/>
    <material name="campfire_stone_mat" texture="rock_granite_tex" rgba="0.40 0.40 0.42 1.0"/>
    <material name="campfire_ember_mat" rgba="0.98 0.35 0.05 1.0" emission="0.85"/>

    <!-- Wetland & Desert Vegetation -->
    <material name="reed_green_mat" rgba="0.26 0.48 0.18 1.0" roughness="0.90"/>
    <material name="lily_flower_pink" rgba="0.98 0.65 0.75 1.0" emission="0.20"/>
    <material name="lily_flower_white" rgba="0.98 0.98 0.95 1.0" emission="0.20"/>
    <material name="cactus_flower_yellow" rgba="0.98 0.90 0.15 1.0" emission="0.30"/>

    <!-- Perimeter Mountain Cliffs -->
    <material name="mountain_rock_mat" texture="rock_granite_tex" texrepeat="6 6" rgba="0.52 0.52 0.54 1.0" reflectance="0.15" roughness="0.85"/>
    <material name="canyon_red_mat" texture="rock_granite_tex" texrepeat="4 4" rgba="0.65 0.42 0.30 1.0" reflectance="0.15" roughness="0.85"/>

    <!-- Battery Kiosk Hardware & Docking Pad Materials -->
    <material name="concrete_pad_mat" texture="concrete_pad_tex" texrepeat="2 2" rgba="0.82 0.82 0.84 1.0" reflectance="0.12" roughness="0.85"/>
    <material name="kiosk_pedestal_mat" rgba="0.25 0.28 0.32 1.0" reflectance="0.25"/>
    <material name="kiosk_cabinet_mat" rgba="0.92 0.93 0.95 1.0" reflectance="0.30"/>
    <material name="kiosk_screen_mat" texture="kiosk_screen_tex" rgba="1 1 1 1" emission="0.45"/>
    <material name="kiosk_lockers_mat" texture="kiosk_lockers_tex" rgba="1 1 1 1" reflectance="0.25"/>
    <material name="kiosk_blue_accent" rgba="0.12 0.45 0.85 1.0" reflectance="0.40"/>
    <material name="solar_roof_mat" rgba="0.22 0.28 0.38 1.0" reflectance="0.60" specular="0.8"/>
    <material name="kiosk_led_green" rgba="0.10 0.95 0.25 1.0" emission="0.9"/>
    <material name="hazard_yellow_mat" rgba="0.95 0.80 0.10 1.0" emission="0.25"/>
    <material name="utility_gray_mat" rgba="0.35 0.38 0.42 1.0" reflectance="0.25"/>

    <!-- Honda e:TECHNOLOGY Autonomous Battery Swap Locker Station Materials (Matching Reference Image) -->
    <material name="honda_white_fascia" rgba="0.95 0.96 0.98 1.0" reflectance="0.50" specular="0.80" roughness="0.20"/>
    <material name="honda_cabinet_dark" rgba="0.20 0.22 0.26 1.0" reflectance="0.22" specular="0.35" roughness="0.50"/>
    <material name="honda_bay_pocket"   rgba="0.07 0.08 0.10 1.0" reflectance="0.12" roughness="0.70"/>
    <material name="honda_slot_blue_led" rgba="0.05 0.75 1.00 1.0" emission="1.00"/>
    <material name="honda_battery_body" rgba="0.13 0.14 0.16 1.0" reflectance="0.25" roughness="0.40"/>
    <material name="honda_handle_blue"  rgba="0.08 0.55 0.98 1.0" emission="0.55" specular="0.70"/>
    <material name="honda_brand_teal"   rgba="0.05 0.90 0.95 1.0" emission="0.85"/>
    <material name="honda_grille_gray"  rgba="0.15 0.16 0.18 1.0" roughness="0.60"/>

    <!-- Robot Chassis & Accent Materials -->
    <material name="chassis_mat" rgba="0.16 0.18 0.20 1.0" reflectance="0.35" roughness="0.55"/>
    <material name="foot_rubber" rgba="0.10 0.10 0.12 1.0" roughness="0.95"/>
    <material name="wheel_mat" rgba="0.12 0.12 0.14 1.0" roughness="0.95"/>
    <material name="rim_alloy_mat" rgba="0.75 0.78 0.82 1.0" reflectance="0.70" specular="0.90" roughness="0.20"/>
    <material name="sensor_mat" rgba="0.08 0.08 0.10 1.0" specular="0.9"/>
    <material name="headlight_lens_mat" rgba="0.95 0.98 1.0 1.0" emission="1.0"/>
    <material name="battery_light" rgba="0.10 0.95 0.25 1.0" emission="1.0"/>
    <material name="battery_halo_mat" rgba="0.10 0.95 0.25 0.35" emission="0.6"/>
    <material name="scan_core_mat" rgba="0.15 0.85 0.95 1.0" emission="0.85"/>
    <material name="carapace_accent_orange" rgba="0.85 0.45 0.10 1.0" emission="0.35" reflectance="0.40"/>
    <material name="carapace_titanium_trim" rgba="0.75 0.78 0.82 1.0" reflectance="0.60" specular="0.75"/>
    <material name="carapace_mat" rgba="0.16 0.18 0.22 1.0" reflectance="0.45" specular="0.70" roughness="0.35"/>
    <material name="battery_box_mat" rgba="0.11 0.12 0.14 1.0" reflectance="0.30" specular="0.60" roughness="0.45"/>
    <material name="pocket_channel_mat" rgba="0.13 0.14 0.16 1.0" reflectance="0.20" roughness="0.65"/>
    <material name="excavator_yellow_mat" rgba="0.95 0.75 0.05 1.0" reflectance="0.40" specular="0.65"/>
    <material name="excavator_tracks_mat" rgba="0.18 0.18 0.20 1.0" roughness="0.90"/>
    <material name="obelisk_hieroglyph_mat" rgba="0.85 0.65 0.45 1.0" roughness="0.85"/>
    <material name="container_teal" rgba="0.12 0.48 0.52 1.0" reflectance="0.30"/>
    <material name="container_orange" rgba="0.85 0.38 0.10 1.0" reflectance="0.30"/>

    <!-- 5-Segment LED Battery Gauge Materials -->
    <material name="bat_led_mat_1" rgba="0.10 0.98 0.25 1.0" emission="0.95"/>
    <material name="bat_led_mat_2" rgba="0.10 0.98 0.25 1.0" emission="0.95"/>
    <material name="bat_led_mat_3" rgba="0.10 0.98 0.25 1.0" emission="0.95"/>
    <material name="bat_led_mat_4" rgba="0.10 0.98 0.25 1.0" emission="0.95"/>
    <material name="bat_led_mat_5" rgba="0.10 0.98 0.25 1.0" emission="0.95"/>

    <!-- 3D LiDAR Visual Materials -->
    <material name="lidar_laser_mat" rgba="0.05 0.98 0.92 0.95" emission="1.0"/>
    <material name="lidar_cone_mat" rgba="0.05 0.98 0.92 0.18" emission="0.65"/>
    <material name="lidar_wave_ring_mat" rgba="0.05 0.98 0.92 0.35" emission="0.80"/>

    <!-- Environmental Materials -->
    <material name="road_marker_amber" rgba="0.98 0.70 0.05 1.0" emission="0.80"/>
    <material name="sign_green_mat" rgba="0.05 0.45 0.18 1.0" reflectance="0.25"/>
    <material name="sign_post_metal" rgba="0.75 0.75 0.78 1.0" reflectance="0.50"/>
    <material name="antenna_light_red" rgba="0.98 0.05 0.05 1.0" emission="1.0"/>
    <material name="telemetry_beacon_blue" rgba="0.10 0.65 0.98 1.0" emission="0.95"/>
  </asset>

  <default>
    <default class="robot_internal">
      <geom contype="0" conaffinity="0" friction="1.5 0.05 0.001"/>
      <joint damping="2.5" armature="0.02"/>
    </default>
    <default class="leg_collision_geom">
      <geom contype="2" conaffinity="1" friction="1.8 0.08 0.005" solref="0.008 1" solimp="0.95 0.99 0.001"/>
      <joint damping="3.2" armature="0.03"/>
    </default>
    <default class="foot_geom">
      <geom type="sphere" size="0.045" material="foot_rubber" contype="2" conaffinity="1" friction="2.8 0.12 0.008" solref="0.005 1" solimp="0.95 0.99 0.001"/>
    </default>
    <default class="wheel_geom">
      <geom type="cylinder" size="0.090 0.035" euler="1.5707963 0 0" material="wheel_mat" contype="2" conaffinity="1" friction="2.4 0.08 0.005" solref="0.008 1" solimp="0.95 0.99 0.001"/>
    </default>
    <default class="visual_only">
      <geom contype="0" conaffinity="0" density="0.01"/>
    </default>
  </default>

  <worldbody>
    <!-- Sunlight Rig -->
    <light name="sun" pos="6.0 -4.0 18.0" dir="-0.35 0.25 -0.9" diffuse="0.95 0.92 0.86" specular="0.35 0.35 0.35" castshadow="true"/>
    <light name="sky_fill" pos="-8.0 8.0 16.0" dir="0.3 -0.3 -0.9" diffuse="0.35 0.42 0.52" specular="0.1 0.1 0.1" castshadow="false"/>

    <!-- Master Unified Ground Terrain -->
    <geom name="ground" type="plane" size="36.0 36.0 0.1" material="world_base_mat" contype="1" conaffinity="7" friction="1.5 0.05 0.002"/>

    <!-- ================= 4 VASTLY ENRICHED DISTINCT BIOME GROUND ZONES ================= -->
    <!-- Place 1: Pine Forest Moss & Soil Ground Zone (Top-Left) -->
    <geom name="zone_floor_p1" type="box" size="9.5 9.0 0.004" pos="-19.0 17.0 0.004" material="forest_ground_mat" contype="0" conaffinity="0"/>
    <geom name="zone_trail_p1" type="box" size="7.0 0.8 0.005" pos="-18.0 16.0 0.005" material="dirt_trail_mat" contype="0" conaffinity="0"/>

    <!-- Place 2: Granite Quarry Broken Bedrock Ground Zone (Top-Right) -->
    <geom name="zone_floor_p2" type="box" size="9.5 9.0 0.004" pos="19.0 17.0 0.004" material="quarry_ground_mat" contype="0" conaffinity="0"/>

    <!-- Place 3: Wet Mud Marsh Ground Zone (Bottom-Left) -->
    <geom name="zone_floor_p3" type="box" size="9.5 8.0 0.004" pos="-19.0 -12.0 0.004" material="mud_marsh_ground_mat" contype="0" conaffinity="0"/>
    <!-- 3 Glossy Reflective Wetland Water Ponds -->
    <geom name="pond_p3_1" type="box" size="4.5 3.0 0.006" pos="-19.5 -13.0 0.006" material="marsh_water_mat" contype="0" conaffinity="0"/>
    <geom name="pond_p3_2" type="cylinder" size="2.5 0.006" pos="-15.0 -8.5 0.006" material="marsh_water_mat" contype="0" conaffinity="0"/>
    <geom name="pond_p3_3" type="cylinder" size="2.0 0.006" pos="-23.0 -10.0 0.006" material="marsh_water_mat" contype="0" conaffinity="0"/>

    <!-- Place 4: Golden Desert Sand Dunes Ground Zone (Bottom-Right) -->
    <geom name="zone_floor_p4" type="box" size="9.5 8.0 0.004" pos="19.0 -12.0 0.004" material="desert_sand_ground_mat" contype="0" conaffinity="0"/>
    <!-- Desert Sand Dune Crests -->
    <geom name="dune_ridge_1" type="ellipsoid" size="5.5 1.4 0.18" pos="20.0 -7.0 0.08" euler="0 0 0.25" material="desert_sand_ground_mat" contype="0" conaffinity="0"/>
    <geom name="dune_ridge_2" type="ellipsoid" size="6.0 1.6 0.22" pos="21.0 -15.5 0.10" euler="0 0 -0.15" material="desert_sand_ground_mat" contype="0" conaffinity="0"/>

    <!-- ================= PAVED ASPHALT ARTERIAL HIGHWAY NETWORK ================= -->
    <!-- 1. Central North-South Main Highway (Y from -24.0 to +24.0) -->
    <geom name="hwy_center_main" type="box" size="1.60 23.0 0.003" pos="0.0 -1.0 0.003" material="asphalt_highway_mat" contype="0" conaffinity="0"/>
    <geom name="hwy_center_line" type="box" size="0.06 23.0 0.005" pos="0.0 -1.0 0.005" material="road_stripe_yellow" contype="0" conaffinity="0"/>
    <geom name="hwy_center_edge_l" type="box" size="0.04 23.0 0.005" pos="-1.50 -1.0 0.005" material="road_stripe_white" contype="0" conaffinity="0"/>
    <geom name="hwy_center_edge_r" type="box" size="0.04 23.0 0.005" pos=" 1.50 -1.0 0.005" material="road_stripe_white" contype="0" conaffinity="0"/>

    <!-- 2. North East-West Cross Highway at y = 16.0 (Connecting Place 1 and Place 2) -->
    <geom name="hwy_north_cross" type="box" size="23.0 1.50 0.003" pos="0.0 16.0 0.003" material="asphalt_highway_mat" contype="0" conaffinity="0"/>
    <geom name="hwy_north_line"  type="box" size="23.0 0.06 0.005" pos="0.0 16.0 0.005" material="road_stripe_yellow" contype="0" conaffinity="0"/>
    <geom name="hwy_north_edge_t" type="box" size="23.0 0.04 0.005" pos="0.0 17.4 0.005" material="road_stripe_white" contype="0" conaffinity="0"/>
    <geom name="hwy_north_edge_b" type="box" size="23.0 0.04 0.005" pos="0.0 14.6 0.005" material="road_stripe_white" contype="0" conaffinity="0"/>

    <!-- 3. South East-West Cross Highway at y = -10.0 (Connecting Place 3 and Place 4) -->
    <geom name="hwy_south_cross" type="box" size="23.0 1.50 0.003" pos="0.0 -10.0 0.003" material="asphalt_highway_mat" contype="0" conaffinity="0"/>
    <geom name="hwy_south_line"  type="box" size="23.0 0.06 0.005" pos="0.0 -10.0 0.005" material="road_stripe_yellow" contype="0" conaffinity="0"/>
    <geom name="hwy_south_edge_t" type="box" size="23.0 0.04 0.005" pos="0.0 -8.6 0.005" material="road_stripe_white" contype="0" conaffinity="0"/>
    <geom name="hwy_south_edge_b" type="box" size="23.0 0.04 0.005" pos="0.0 -11.4 0.005" material="road_stripe_white" contype="0" conaffinity="0"/>

    <!-- 4. West Arterial Bypass Highway at x = -10.0 (Y from -10.0 to +16.0) -->
    <geom name="hwy_west_bypass" type="box" size="1.40 13.0 0.003" pos="-10.0 3.0 0.003" material="asphalt_highway_mat" contype="0" conaffinity="0"/>
    <geom name="hwy_west_line"   type="box" size="0.05 13.0 0.005" pos="-10.0 3.0 0.005" material="road_stripe_yellow" contype="0" conaffinity="0"/>

    <!-- 5. East Arterial Bypass Highway at x = +10.0 (Y from -10.0 to +16.0) -->
    <geom name="hwy_east_bypass" type="box" size="1.40 13.0 0.003" pos=" 10.0 3.0 0.003" material="asphalt_highway_mat" contype="0" conaffinity="0"/>
    <geom name="hwy_east_line"   type="box" size="0.05 13.0 0.005" pos=" 10.0 3.0 0.005" material="road_stripe_yellow" contype="0" conaffinity="0"/>

    <!-- 6. Diagonal Connector Roads linking Base Depot Apron to Arteries -->
    <geom name="hwy_diag_sw" type="box" size="1.40 4.5 0.003" pos="-4.5 -15.5 0.003" euler="0 0  0.65" material="asphalt_highway_mat" contype="0" conaffinity="0"/>
    <geom name="hwy_diag_se" type="box" size="1.40 4.5 0.003" pos=" 4.5 -15.5 0.003" euler="0 0 -0.65" material="asphalt_highway_mat" contype="0" conaffinity="0"/>

    <!-- ================= CONTINUOUS PERIMETER MOUNTAINS (50+ PEAKS) ================= -->
"""
    # Generate 15 North Mountain Peaks
    for k, mx in enumerate(np.linspace(-35.0, 35.0, 15)):
        mz = 6.0 + 4.5 * math.sin(k * 0.7)
        rad = 3.2 + 1.2 * math.cos(k * 0.5)
        mat = "mountain_rock_mat" if k % 2 == 0 else "canyon_red_mat"
        xml += f'    <geom name="mount_n_{k}" type="cylinder" size="{rad:.2f} {mz:.2f}" pos="{mx:.1f} 35.8 {mz:.2f}" material="{mat}" contype="1" conaffinity="7"/>\n'
        xml += f'    <geom name="mount_n_b_{k}" type="cylinder" size="{rad*1.3:.2f} {mz*0.6:.2f}" pos="{mx:.1f} 34.2 {mz*0.6:.2f}" material="{mat}" contype="1" conaffinity="7"/>\n'

    # Generate 15 South Mountain Peaks
    for k, mx in enumerate(np.linspace(-35.0, 35.0, 15)):
        mz = 5.5 + 4.0 * math.cos(k * 0.8)
        rad = 3.0 + 1.0 * math.sin(k * 0.6)
        mat = "canyon_red_mat" if k % 2 == 0 else "mountain_rock_mat"
        xml += f'    <geom name="mount_s_{k}" type="cylinder" size="{rad:.2f} {mz:.2f}" pos="{mx:.1f} -35.8 {mz:.2f}" material="{mat}" contype="1" conaffinity="7"/>\n'
        xml += f'    <geom name="mount_s_b_{k}" type="cylinder" size="{rad*1.3:.2f} {mz*0.6:.2f}" pos="{mx:.1f} -34.2 {mz*0.6:.2f}" material="{mat}" contype="1" conaffinity="7"/>\n'

    # Generate 13 West Mountain Peaks
    for k, my in enumerate(np.linspace(-33.0, 33.0, 13)):
        mz = 6.5 + 3.8 * math.sin(k * 0.9)
        rad = 3.1 + 0.9 * math.cos(k * 0.7)
        xml += f'    <geom name="mount_w_{k}" type="cylinder" size="{rad:.2f} {mz:.2f}" pos="-35.8 {my:.1f} {mz:.2f}" material="mountain_rock_mat" contype="1" conaffinity="7"/>\n'

    # Generate 13 East Mountain Peaks
    for k, my in enumerate(np.linspace(-33.0, 33.0, 13)):
        mz = 7.0 + 4.2 * math.cos(k * 0.75)
        rad = 3.3 + 1.1 * math.sin(k * 0.65)
        xml += f'    <geom name="mount_e_{k}" type="cylinder" size="{rad:.2f} {mz:.2f}" pos="35.8 {my:.1f} {mz:.2f}" material="canyon_red_mat" contype="1" conaffinity="7"/>\n'

    xml += """
    <!-- Perimeter Security Floodlight Towers with Aviation Strobes -->
    <body name="tower_nw" pos="-31.0 31.0 0">
      <geom type="cylinder" size="0.12 6.0" pos="0 0 6.0" material="field_station_metal" contype="1" conaffinity="7"/>
      <geom type="box" size="0.90 0.90 0.08" pos="0 0 12.0" material="camp_wood_mat" contype="0" conaffinity="0"/>
      <geom type="sphere" size="0.12" pos="0 0 12.2" material="antenna_light_red" contype="0" conaffinity="0"/>
      <geom type="cylinder" size="0.08 0.15" pos="0.5 0.5 12.1" euler="0.6 0.6 0" material="headlight_lens_mat" contype="0" conaffinity="0"/>
    </body>
    <body name="tower_ne" pos="31.0 31.0 0">
      <geom type="cylinder" size="0.12 6.0" pos="0 0 6.0" material="field_station_metal" contype="1" conaffinity="7"/>
      <geom type="box" size="0.90 0.90 0.08" pos="0 0 12.0" material="camp_wood_mat" contype="0" conaffinity="0"/>
      <geom type="sphere" size="0.12" pos="0 0 12.2" material="antenna_light_red" contype="0" conaffinity="0"/>
      <geom type="cylinder" size="0.08 0.15" pos="-0.5 0.5 12.1" euler="0.6 -0.6 0" material="headlight_lens_mat" contype="0" conaffinity="0"/>
    </body>
    <body name="tower_sw" pos="-31.0 -31.0 0">
      <geom type="cylinder" size="0.12 6.0" pos="0 0 6.0" material="field_station_metal" contype="1" conaffinity="7"/>
      <geom type="box" size="0.90 0.90 0.08" pos="0 0 12.0" material="camp_wood_mat" contype="0" conaffinity="0"/>
      <geom type="sphere" size="0.12" pos="0 0 12.2" material="antenna_light_red" contype="0" conaffinity="0"/>
    </body>
    <body name="tower_se" pos="31.0 -31.0 0">
      <geom type="cylinder" size="0.12 6.0" pos="0 0 6.0" material="field_station_metal" contype="1" conaffinity="7"/>
      <geom type="box" size="0.90 0.90 0.08" pos="0 0 12.0" material="camp_wood_mat" contype="0" conaffinity="0"/>
      <geom type="sphere" size="0.12" pos="0 0 12.2" material="antenna_light_red" contype="0" conaffinity="0"/>
    </body>

    <!-- Highway Directional Overhead Gantries -->
    <body name="gantry_north" pos="0 10.0 0">
      <geom type="cylinder" size="0.08 2.0" pos="-3.6 0 2.0" material="sign_post_metal" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.08 2.0" pos=" 3.6 0 2.0" material="sign_post_metal" contype="1" conaffinity="7"/>
      <geom type="box" size="3.70 0.08 0.08" pos="0 0 4.00" material="sign_post_metal" contype="0" conaffinity="0"/>
      <geom type="box" size="2.60 0.02 0.40" pos="0 0 4.00" material="sign_green_mat" contype="0" conaffinity="0"/>
    </body>
    <body name="gantry_south" pos="0 -14.0 0">
      <geom type="cylinder" size="0.08 2.0" pos="-3.6 0 2.0" material="sign_post_metal" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.08 2.0" pos=" 3.6 0 2.0" material="sign_post_metal" contype="1" conaffinity="7"/>
      <geom type="box" size="3.70 0.08 0.08" pos="0 0 4.00" material="sign_post_metal" contype="0" conaffinity="0"/>
      <geom type="box" size="2.60 0.02 0.40" pos="0 0 4.00" material="sign_green_mat" contype="0" conaffinity="0"/>
    </body>

    <!-- ================= PLACE 1: PINE FOREST & EXPEDITION SCIENCE CAMP (Top-Left) ================= -->
    <!-- Expedition Research Wall Tent (pos: -24.0, 16.0) -->
    <body name="p1_tent" pos="-24.0 16.0 0">
      <geom type="box" size="1.40 1.00 0.75" pos="0 0 0.75" material="tent_canvas_mat" contype="1" conaffinity="7"/>
      <geom type="box" size="1.45 1.05 0.02" pos="0 0 1.52" material="tent_fly_mat" contype="0" conaffinity="0"/>
    </body>

    <!-- Observation Watchtower (pos: -26.0, 22.0) -->
    <body name="p1_watchtower" pos="-26.0 22.0 0">
      <geom type="cylinder" size="0.08 2.2" pos="-1.2 -1.2 2.2" material="pine_trunk_mat" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.08 2.2" pos=" 1.2 -1.2 2.2" material="pine_trunk_mat" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.08 2.2" pos="-1.2  1.2 2.2" material="pine_trunk_mat" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.08 2.2" pos=" 1.2  1.2 2.2" material="pine_trunk_mat" contype="1" conaffinity="7"/>
      <geom type="box" size="1.40 1.40 0.06" pos="0 0 4.40" material="camp_wood_mat" contype="1" conaffinity="7"/>
      <geom type="box" size="1.50 1.50 0.04" pos="0 0 5.60" material="tent_fly_mat" contype="0" conaffinity="0"/>
    </body>

    <!-- Log Cabin Field Station (pos: -25.0, 13.0) -->
    <body name="p1_cabin" pos="-25.0 13.0 0">
      <geom type="box" size="1.80 1.30 0.90" pos="0 0 0.90" material="camp_wood_mat" contype="1" conaffinity="7"/>
      <geom type="box" size="1.95 1.45 0.04" pos="0 0 1.82" material="pine_trunk_mat" contype="0" conaffinity="0"/>
    </body>

    <!-- Central Campfire Ring with Glowing Embers (pos: -18.0, 20.0) -->
    <body name="p1_campfire" pos="-18.0 20.0 0">
      <geom type="cylinder" size="0.65 0.08" pos="0 0 0.08" material="campfire_stone_mat" contype="0" conaffinity="0"/>
      <geom type="cylinder" size="0.45 0.04" pos="0 0 0.12" material="campfire_ember_mat" contype="0" conaffinity="0"/>
      <geom type="cylinder" size="0.06 0.35" pos="0.25 0 0.15" euler="0.3 0.4 0" material="stump_bark_mat" contype="0" conaffinity="0"/>
      <geom type="cylinder" size="0.06 0.35" pos="-0.25 0 0.15" euler="-0.3 0.4 0" material="stump_bark_mat" contype="0" conaffinity="0"/>
    </body>

    <!-- Split-Rail Log Fencing along Camp Boundary -->
    <geom type="cylinder" size="0.05 1.6" pos="-22.0 11.5 0.30" euler="1.5708 0 0" material="camp_wood_mat" contype="1" conaffinity="7"/>
    <geom type="cylinder" size="0.05 1.6" pos="-22.0 11.5 0.60" euler="1.5708 0 0" material="camp_wood_mat" contype="1" conaffinity="7"/>
    <geom type="cylinder" size="0.05 1.6" pos="-18.0 11.5 0.30" euler="1.5708 0 0" material="camp_wood_mat" contype="1" conaffinity="7"/>
    <geom type="cylinder" size="0.05 1.6" pos="-18.0 11.5 0.60" euler="1.5708 0 0" material="camp_wood_mat" contype="1" conaffinity="7"/>

    <!-- Cordwood Timber Ricks (Safely off path at y=10.5) -->
    <body name="p1_wood_rick" pos="-14.5 10.5 0">
      <geom type="box" size="0.80 0.40 0.45" pos="0 0 0.45" material="camp_wood_mat" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.06 0.75" pos="0 -0.15 0.95" euler="0 1.5708 0" material="stump_bark_mat" contype="0" conaffinity="0"/>
    </body>

    <!-- Scientific Weather Station (pos: -13.0, 19.0) -->
    <body name="p1_met_station" pos="-13.0 19.0 0">
      <geom type="cylinder" size="0.03 1.2" pos="0 0 1.2" material="sign_post_metal" contype="1" conaffinity="7"/>
      <geom type="box" size="0.12 0.10 0.14" pos="0 0 1.40" material="utility_gray_mat" contype="0" conaffinity="0"/>
      <geom type="box" size="0.15 0.20 0.01" pos="0 0.15 1.50" euler="0.45 0 0" material="solar_cell_mat" contype="0" conaffinity="0"/>
      <geom type="cylinder" size="0.01 0.20" pos="0 0 2.45" euler="0 1.5708 0" material="field_station_metal" contype="0" conaffinity="0"/>
    </body>

    <!-- Off-Road Camp Buggy (pos: -22.5, 12.0) -->
    <body name="p1_camp_buggy" pos="-22.5 12.0 0" euler="0 0 0.35">
      <geom type="box" size="0.95 0.60 0.25" pos="0 0 0.35" material="field_station_metal" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.18 0.08" pos="0.65 0.65 0.18" euler="1.5708 0 0" material="wheel_mat" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.18 0.08" pos="0.65 -0.65 0.18" euler="1.5708 0 0" material="wheel_mat" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.18 0.08" pos="-0.65 0.65 0.18" euler="1.5708 0 0" material="wheel_mat" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.18 0.08" pos="-0.65 -0.65 0.18" euler="1.5708 0 0" material="wheel_mat" contype="1" conaffinity="7"/>
    </body>

    <!-- Camp Metal Supply Crates & Fuel Drums -->
    <geom type="box" size="0.45 0.35 0.30" pos="-20.5 18.0 0.30" material="crate_metal_mat" contype="1" conaffinity="7"/>
    <geom type="cylinder" size="0.22 0.40" pos="-21.2 18.2 0.40" material="hazard_yellow_mat" contype="1" conaffinity="7"/>
    <geom type="cylinder" size="0.22 0.40" pos="-21.7 18.2 0.40" material="field_station_metal" contype="1" conaffinity="7"/>

    <!-- Field Science Spectrometer Rack & Telemetry Processor (pos: -16.0, 18.5) -->
    <body name="p1_spectrometer" pos="-16.0 18.5 0">
      <geom type="box" size="0.45 0.30 0.55" pos="0 0 0.55" material="utility_gray_mat" contype="1" conaffinity="7"/>
      <geom type="box" size="0.35 0.02 0.25" pos="0 -0.31 0.75" material="kiosk_screen_mat" contype="0" conaffinity="0"/>
      <geom type="cylinder" size="0.02 0.40" pos="0.30 0 1.30" material="field_station_metal" contype="0" conaffinity="0"/>
      <geom type="sphere" size="0.06" pos="0.30 0 1.72" material="scan_core_mat" contype="0" conaffinity="0"/>
    </body>

    <!-- Field Observation Telescope on Carbon-Fiber Tripod (pos: -19.5, 22.5) -->
    <body name="p1_telescope" pos="-19.5 22.5 0">
      <geom type="cylinder" size="0.018 0.65" pos="-0.25 -0.25 0.65" euler="-0.25 -0.25 0" material="field_station_metal" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.018 0.65" pos=" 0.25 -0.25 0.65" euler="-0.25  0.25 0" material="field_station_metal" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.018 0.65" pos=" 0.00  0.30 0.65" euler=" 0.30  0.00 0" material="field_station_metal" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.06 0.45" pos="0 0 1.35" euler="0.35 0 0" material="chassis_mat" contype="0" conaffinity="0"/>
      <geom type="sphere" size="0.058" pos="0 -0.42 1.20" material="headlight_lens_mat" contype="0" conaffinity="0"/>
    </body>

    <!-- Ranger Wooden Picnic Table with Field Lantern (pos: -16.5, 14.0) -->
    <body name="p1_picnic_table" pos="-16.5 14.0 0">
      <geom type="box" size="0.90 0.45 0.04" pos="0 0 0.72" material="camp_wood_mat" contype="1" conaffinity="7"/>
      <geom type="box" size="0.90 0.18 0.04" pos="0 -0.65 0.42" material="camp_wood_mat" contype="1" conaffinity="7"/>
      <geom type="box" size="0.90 0.18 0.04" pos="0  0.65 0.42" material="camp_wood_mat" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.04 0.36" pos="-0.70 0 0.36" material="pine_trunk_mat" contype="0" conaffinity="0"/>
      <geom type="cylinder" size="0.04 0.36" pos=" 0.70 0 0.36" material="pine_trunk_mat" contype="0" conaffinity="0"/>
      <geom type="cylinder" size="0.04 0.08" pos="0.30 0 0.84" material="hazard_yellow_mat" contype="0" conaffinity="0"/>
    </body>

    <!-- Two-Person Expedition Scout Dome Tent (pos: -23.0, 19.5) -->
    <body name="p1_scout_tent" pos="-23.0 19.5 0" euler="0 0 0.45">
      <geom type="ellipsoid" size="0.95 0.80 0.65" pos="0 0 0.55" material="carapace_accent_orange" contype="1" conaffinity="7"/>
    </body>

    <!-- Forestry Map & Information Board (pos: -15.0, 11.5) -->
    <body name="p1_info_board" pos="-15.0 11.5 0">
      <geom type="cylinder" size="0.04 0.90" pos="-0.6 0 0.90" material="pine_trunk_mat" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.04 0.90" pos=" 0.6 0 0.90" material="pine_trunk_mat" contype="1" conaffinity="7"/>
      <geom type="box" size="0.75 0.04 0.45" pos="0 0 1.80" material="camp_wood_mat" contype="1" conaffinity="7"/>
      <geom type="box" size="0.68 0.01 0.38" pos="0 -0.042 1.80" material="kiosk_screen_mat" contype="0" conaffinity="0"/>
    </body>
"""

    # Add 165 pine trees
    for i, t in enumerate(trees):
        pos = t["pos"]
        model = t["model"]
        sc = t["scale"]
        trunk_h = t["trunk_h"]
        e = t["euler"]
        xml += f"""    <body name="p1_tree_{i}" pos="{pos[0]:.2f} {pos[1]:.2f} 0" euler="{e[0]:.2f} {e[1]:.2f} {e[2]:.2f}">
      <geom type="cylinder" size="{0.10*sc:.2f} {trunk_h:.2f}" pos="0 0 {trunk_h:.2f}" material="pine_trunk_mat" contype="1" conaffinity="7"/>
      <geom type="mesh" mesh="{model}_mesh" pos="0 0 {trunk_h*0.35:.2f}" material="pine_foliage_mat" contype="0" conaffinity="0"/>
    </body>\n"""

    # ---------------------------------------------------------
    # PLACE 2: GRANITE QUARRY & MINERAL BASIN
    # ---------------------------------------------------------
    xml += """
    <!-- ================= PLACE 2: GRANITE QUARRY & MINERAL BASIN (Top-Right) ================= -->
    <!-- Heavy Mining Excavator (pos: 15.0, 21.0) -->
    <body name="p2_excavator" pos="15.0 21.0 0" euler="0 0 -0.45">
      <geom type="box" size="1.20 0.35 0.25" pos="0 -0.65 0.25" material="excavator_tracks_mat" contype="1" conaffinity="7"/>
      <geom type="box" size="1.20 0.35 0.25" pos="0  0.65 0.25" material="excavator_tracks_mat" contype="1" conaffinity="7"/>
      <geom type="box" size="1.10 0.90 0.65" pos="0 0 1.15" material="excavator_yellow_mat" contype="1" conaffinity="7"/>
      <geom type="box" size="1.40 0.12 0.18" pos="1.40 0.10 2.20" euler="0 0.55 0" material="excavator_yellow_mat" contype="0" conaffinity="0"/>
      <geom type="box" size="0.95 0.10 0.14" pos="2.60 0.10 1.70" euler="0 -0.65 0" material="excavator_yellow_mat" contype="0" conaffinity="0"/>
      <geom type="box" size="0.45 0.35 0.30" pos="3.10 0.10 0.95" material="chassis_mat" contype="1" conaffinity="7"/>
    </body>

    <!-- Heavy Quarry Ore Hauler Dump Truck (pos: 24.0, 21.0) -->
    <body name="p2_dump_truck" pos="24.0 21.0 0" euler="0 0 0.85">
      <geom type="box" size="1.60 1.10 0.40" pos="0 0 0.85" material="utility_gray_mat" contype="1" conaffinity="7"/>
      <geom type="box" size="0.65 0.95 0.70" pos="-0.85 0 1.55" material="excavator_yellow_mat" contype="1" conaffinity="7"/>
      <geom type="box" size="1.20 1.05 0.55" pos="0.55 0 1.70" euler="0 0.18 0" material="excavator_yellow_mat" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.38 0.18" pos="1.10 1.20 0.38" euler="1.5708 0 0" material="wheel_mat" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.38 0.18" pos="1.10 -1.20 0.38" euler="1.5708 0 0" material="wheel_mat" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.38 0.18" pos="-1.10 1.20 0.38" euler="1.5708 0 0" material="wheel_mat" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.38 0.18" pos="-1.10 -1.20 0.38" euler="1.5708 0 0" material="wheel_mat" contype="1" conaffinity="7"/>
    </body>

    <!-- Quarry Derrick Lattice Crane (pos: 20.5, 22.0) -->
    <body name="p2_crane" pos="20.5 22.0 0">
      <geom type="cylinder" size="0.12 2.80" pos="0 0 2.80" material="excavator_yellow_mat" contype="1" conaffinity="7"/>
      <geom type="box" size="2.80 0.10 0.10" pos="1.20 0 5.60" material="excavator_yellow_mat" contype="0" conaffinity="0"/>
      <geom type="cylinder" size="0.02 1.60" pos="2.40 0 3.90" material="field_station_metal" contype="0" conaffinity="0"/>
      <geom type="box" size="0.25 0.25 0.15" pos="2.40 0 2.20" material="chassis_mat" contype="0" conaffinity="0"/>
    </body>

    <!-- 12-Meter Aggregate Conveyor System (pos: 23.0, 17.5) -->
    <body name="p2_conveyor" pos="23.0 17.5 0" euler="0 0.25 0.65">
      <geom type="box" size="3.20 0.35 0.08" pos="0 0 1.40" material="utility_gray_mat" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.05 0.95" pos="-2.2 0 0.95" material="field_station_metal" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.05 1.65" pos=" 2.2 0 1.65" material="field_station_metal" contype="1" conaffinity="7"/>
    </body>

    <!-- Site Operations Office Cabin (pos: 25.0, 13.0) -->
    <body name="p2_office" pos="25.0 13.0 0">
      <geom type="box" size="1.80 1.20 0.95" pos="0 0 0.95" material="kiosk_cabinet_mat" contype="1" conaffinity="7"/>
      <geom type="box" size="0.80 0.02 0.40" pos="0 -1.21 1.10" material="kiosk_screen_mat" contype="0" conaffinity="0"/>
    </body>

    <!-- Geological Core Sampling Trays & Optical Transit (pos: 23.5, 16.0) -->
    <body name="p2_core_station" pos="23.5 16.0 0">
      <geom type="box" size="0.55 0.35 0.05" pos="0 0 0.05" material="camp_wood_mat" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.02 0.65" pos="0.85 0 0.65" material="hazard_yellow_mat" contype="1" conaffinity="7"/>
      <geom type="box" size="0.10 0.08 0.08" pos="0.85 0 1.35" material="carapace_accent_orange" contype="0" conaffinity="0"/>
    </body>

    <!-- Heavy Industrial Rock Crusher Hopper Unit (pos: 17.5, 23.5) -->
    <body name="p2_rock_crusher" pos="17.5 23.5 0">
      <geom type="box" size="1.30 1.00 0.85" pos="0 0 1.45" material="utility_gray_mat" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.08 0.70" pos="-1.0 -0.8 0.70" material="field_station_metal" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.08 0.70" pos=" 1.0 -0.8 0.70" material="field_station_metal" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.08 0.70" pos="-1.0  0.8 0.70" material="field_station_metal" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.08 0.70" pos=" 1.0  0.8 0.70" material="field_station_metal" contype="1" conaffinity="7"/>
      <geom type="box" size="1.10 0.20 0.40" pos="0 -0.95 0.85" euler="0.6 0 0" material="excavator_yellow_mat" contype="0" conaffinity="0"/>
    </body>

    <!-- Vibratory Ore Grading Screen Deck (pos: 24.5, 18.5) -->
    <body name="p2_sorting_screen" pos="24.5 18.5 0" euler="0 0.30 0.80">
      <geom type="box" size="1.60 0.55 0.08" pos="0 0 1.20" material="field_station_metal" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.05 0.60" pos="-1.1 0 0.60" material="field_station_metal" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.05 1.10" pos=" 1.1 0 1.10" material="field_station_metal" contype="1" conaffinity="7"/>
    </body>

    <!-- High-Mast Mobile Floodlight Rig (pos: 13.5, 13.5) -->
    <body name="p2_floodlight_rig" pos="13.5 13.5 0">
      <geom type="box" size="0.45 0.40 0.25" pos="0 0 0.25" material="excavator_yellow_mat" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.04 1.80" pos="0 0 2.05" material="field_station_metal" contype="1" conaffinity="7"/>
      <geom type="box" size="0.30 0.08 0.14" pos="0 0 3.85" material="field_station_metal" contype="0" conaffinity="0"/>
      <geom type="cylinder" size="0.07 0.05" pos="-0.16 0.08 3.85" euler="0.4 0 0" material="headlight_lens_mat" contype="0" conaffinity="0"/>
      <geom type="cylinder" size="0.07 0.05" pos=" 0.16 0.08 3.85" euler="0.4 0 0" material="headlight_lens_mat" contype="0" conaffinity="0"/>
    </body>

    <!-- Steel Cargo Supply Cache & Lubricant Barrels (pos: 22.0, 11.5) -->
    <body name="p2_supply_cache" pos="22.0 11.5 0">
      <geom type="box" size="0.65 0.45 0.35" pos="0 0 0.35" material="container_orange" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.24 0.45" pos="0.85 0 0.45" material="hazard_yellow_mat" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.24 0.45" pos="0.85 0.55 0.45" material="utility_gray_mat" contype="1" conaffinity="7"/>
    </body>
"""

    # Add rock slabs with real contact
    for j, s in enumerate(slabs):
        pos = s["pos"]
        size = s["size"]
        e = s["euler"]
        xml += f"""    <geom name="p2_slab_{j}" type="box" size="{size[0]:.2f} {size[1]:.2f} {size[2]:.3f}" pos="{pos[0]:.2f} {pos[1]:.2f} {pos[2]:.3f}" euler="{e[0]:.2f} {e[1]:.2f} {e[2]:.2f}" material="broken_slab_mat" contype="1" conaffinity="7" friction="2.2 0.1 0.01"/>\n"""

    # ---------------------------------------------------------
    # PLACE 3: CHURNED MUD MARSH & WETLAND LAGOON
    # ---------------------------------------------------------
    xml += """
    <!-- ================= PLACE 3: MUD MARSH & WETLAND ESTUARY (Bottom-Left) ================= -->
    <!-- Wetland Timber Boardwalk Walkway -->
    <geom name="p3_boardwalk_1" type="box" size="4.20 0.55 0.02" pos="-18.0 -12.5 0.02" material="camp_wood_mat" contype="0" conaffinity="0"/>
    <geom name="p3_boardwalk_2" type="box" size="0.55 3.50 0.02" pos="-14.5 -12.5 0.02" material="camp_wood_mat" contype="0" conaffinity="0"/>
    <geom name="p3_boardwalk_3" type="box" size="3.20 0.55 0.02" pos="-21.5 -15.5 0.02" material="camp_wood_mat" contype="0" conaffinity="0"/>

    <!-- Estuary Mooring Pier & Research Stilt Hut 1 (pos: -21.5, -15.0) -->
    <body name="p3_stilt_hut" pos="-21.5 -15.0 0">
      <geom type="cylinder" size="0.08 0.85" pos="-1.1 -1.1 0.85" material="camp_wood_mat" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.08 0.85" pos=" 1.1 -1.1 0.85" material="camp_wood_mat" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.08 0.85" pos="-1.1  1.1 0.85" material="camp_wood_mat" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.08 0.85" pos=" 1.1  1.1 0.85" material="camp_wood_mat" contype="1" conaffinity="7"/>
      <geom type="box" size="1.30 1.30 0.75" pos="0 0 2.45" material="camp_wood_mat" contype="1" conaffinity="7"/>
      <geom type="box" size="1.45 1.45 0.04" pos="0 0 3.25" material="tent_fly_mat" contype="0" conaffinity="0"/>
    </body>

    <!-- Research Stilt Hut 2 / Observation Blind (pos: -23.5, -9.5) -->
    <body name="p3_stilt_hut_2" pos="-23.5 -9.5 0">
      <geom type="cylinder" size="0.08 0.85" pos="-0.9 -0.9 0.85" material="camp_wood_mat" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.08 0.85" pos=" 0.9 -0.9 0.85" material="camp_wood_mat" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.08 0.85" pos="-0.9  0.9 0.85" material="camp_wood_mat" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.08 0.85" pos=" 0.9  0.9 0.85" material="camp_wood_mat" contype="1" conaffinity="7"/>
      <geom type="box" size="1.10 1.10 0.65" pos="0 0 2.30" material="camp_wood_mat" contype="1" conaffinity="7"/>
    </body>

    <!-- Water Quality Telemetry Buoy (pos: -14.5, -6.0) -->
    <body name="p3_buoy" pos="-14.5 -6.0 0.05">
      <geom type="cylinder" size="0.32 0.09" pos="0 0 0.09" material="hazard_yellow_mat" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.02 0.45" pos="0 0 0.50" material="field_station_metal" contype="0" conaffinity="0"/>
      <geom type="sphere" size="0.06" pos="0 0 0.98" material="telemetry_beacon_blue" contype="0" conaffinity="0"/>
    </body>

    <!-- Water Lily Clusters & Cattails -->
    <geom type="cylinder" size="0.22 0.002" pos="-17.0 -9.0 0.01" material="reed_green_mat" contype="0" conaffinity="0"/>
    <geom type="sphere" size="0.04" pos="-17.0 -9.0 0.03" material="lily_flower_pink" contype="0" conaffinity="0"/>
    <geom type="cylinder" size="0.22 0.002" pos="-19.5 -11.5 0.01" material="reed_green_mat" contype="0" conaffinity="0"/>
    <geom type="sphere" size="0.04" pos="-19.5 -11.5 0.03" material="lily_flower_white" contype="0" conaffinity="0"/>
    <geom type="cylinder" size="0.22 0.002" pos="-22.0 -14.0 0.01" material="reed_green_mat" contype="0" conaffinity="0"/>
    <geom type="sphere" size="0.04" pos="-22.0 -14.0 0.03" material="lily_flower_pink" contype="0" conaffinity="0"/>

    <!-- Wetland Mooring Pier & Marine Cleats (pos: -13.5, -6.0) -->
    <body name="p3_mooring_pier" pos="-13.5 -6.0 0">
      <geom type="box" size="0.55 1.80 0.03" pos="0 0 0.15" material="camp_wood_mat" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.06 0.25" pos="-0.45 -1.5 0.25" material="pine_trunk_mat" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.06 0.25" pos=" 0.45 -1.5 0.25" material="pine_trunk_mat" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.06 0.25" pos="-0.45  1.5 0.25" material="pine_trunk_mat" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.06 0.25" pos=" 0.45  1.5 0.25" material="pine_trunk_mat" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.16 0.03" pos="0.45 0 0.38" euler="0 1.5708 0" material="traffic_cone_orange" contype="0" conaffinity="0"/>
    </body>

    <!-- Moored Expedition Flatboat Skiff (pos: -15.0, -5.5) -->
    <body name="p3_rowboat" pos="-15.0 -5.5 0.08" euler="0 0 0.25">
      <geom type="box" size="0.45 1.10 0.14" pos="0 0 0.10" material="camp_wood_mat" contype="1" conaffinity="7"/>
      <geom type="box" size="0.40 0.15 0.03" pos="0 0 0.20" material="camp_wood_mat" contype="0" conaffinity="0"/>
    </body>

    <!-- Hydrological Multi-Depth Floating Sensor Buoy (pos: -20.5, -10.5) -->
    <body name="p3_hydro_buoy" pos="-20.5 -10.5 0.05">
      <geom type="cylinder" size="0.30 0.10" pos="0 0 0.10" material="container_teal" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.02 0.50" pos="0 0 0.55" material="field_station_metal" contype="0" conaffinity="0"/>
      <geom type="sphere" size="0.07" pos="0 0 1.08" material="scan_core_mat" contype="0" conaffinity="0"/>
    </body>
"""

    # ---------------------------------------------------------
    # PLACE 4: GOLDEN DESERT & ANCIENT RUINS
    # ---------------------------------------------------------
    xml += """
    <!-- ================= PLACE 4: GOLDEN DESERT & ANCIENT RUINS (Bottom-Right) ================= -->
    <!-- Classical Sandstone Colonnade Columns -->
    <geom name="p4_col_1"  type="cylinder" size="0.25 1.50" pos="21.0 -7.0  1.50" material="sandstone_mat" contype="1" conaffinity="7"/>
    <geom name="p4_col_2"  type="cylinder" size="0.25 1.50" pos="21.0 -9.5  1.50" material="sandstone_mat" contype="1" conaffinity="7"/>
    <geom name="p4_col_3"  type="cylinder" size="0.25 1.50" pos="21.0 -12.0 1.50" material="sandstone_mat" contype="1" conaffinity="7"/>
    <geom name="p4_col_4"  type="cylinder" size="0.25 1.50" pos="24.0 -7.0  1.50" material="sandstone_mat" contype="1" conaffinity="7"/>
    <geom name="p4_col_5"  type="cylinder" size="0.25 1.50" pos="24.0 -9.5  1.50" material="sandstone_mat" contype="1" conaffinity="7"/>
    <geom name="p4_col_6"  type="cylinder" size="0.25 1.50" pos="24.0 -12.0 1.50" material="sandstone_mat" contype="1" conaffinity="7"/>
    <geom name="p4_col_7"  type="cylinder" size="0.25 1.50" pos="18.0 -5.0  1.50" material="sandstone_mat" contype="1" conaffinity="7"/>
    <geom name="p4_col_8"  type="cylinder" size="0.25 1.50" pos="18.0 -12.0 1.50" material="sandstone_mat" contype="1" conaffinity="7"/>

    <!-- Monumental Collapsed Ancient Stone Archway (pos: 19.0, -14.0) -->
    <body name="p4_arch" pos="19.0 -14.0 0">
      <geom type="box" size="0.30 0.30 1.40" pos="-1.2 0 1.40" material="sandstone_mat" contype="1" conaffinity="7"/>
      <geom type="box" size="0.30 0.30 1.40" pos=" 1.2 0 1.40" material="sandstone_mat" contype="1" conaffinity="7"/>
      <geom type="box" size="1.60 0.35 0.22" pos="0 0 2.95" material="sandstone_mat" contype="1" conaffinity="7"/>
    </body>

    <!-- Monumental Temple Gate Pylons with Winged Sun Relief (pos: 16.0, -6.5) -->
    <body name="p4_pylon_gate" pos="16.0 -6.5 0">
      <geom type="box" size="0.45 0.45 1.75" pos="-1.6 0 1.75" material="sandstone_mat" contype="1" conaffinity="7"/>
      <geom type="box" size="0.45 0.45 1.75" pos=" 1.6 0 1.75" material="sandstone_mat" contype="1" conaffinity="7"/>
      <geom type="box" size="2.20 0.50 0.22" pos="0 0 3.65" material="sandstone_mat" contype="1" conaffinity="7"/>
      <geom type="sphere" size="0.16" pos="0 -0.52 3.65" material="hazard_yellow_mat" contype="0" conaffinity="0"/>
    </body>

    <!-- Ceremonial Offering Altar with Bronze Brazier & Embers (pos: 21.5, -11.5) -->
    <body name="p4_ceremonial_altar" pos="21.5 -11.5 0">
      <geom type="box" size="0.75 0.55 0.40" pos="0 0 0.40" material="sandstone_mat" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.32 0.08" pos="0 0 0.88" material="campfire_stone_mat" contype="0" conaffinity="0"/>
      <geom type="sphere" size="0.15" pos="0 0 0.94" material="campfire_ember_mat" contype="0" conaffinity="0"/>
    </body>

    <!-- Archaeological Dig Excavation Trench & Sifting Grid (pos: 15.0, -12.5) -->
    <body name="p4_dig_trench" pos="15.0 -12.5 0">
      <geom type="box" size="1.20 1.20 0.02" pos="0 0 0.02" material="dune_sand_mat" contype="0" conaffinity="0"/>
      <geom type="cylinder" size="0.02 0.35" pos="-1.1 -1.1 0.35" material="camp_wood_mat" contype="0" conaffinity="0"/>
      <geom type="cylinder" size="0.02 0.35" pos=" 1.1 -1.1 0.35" material="camp_wood_mat" contype="0" conaffinity="0"/>
      <geom type="cylinder" size="0.02 0.35" pos="-1.1  1.1 0.35" material="camp_wood_mat" contype="0" conaffinity="0"/>
      <geom type="cylinder" size="0.02 0.35" pos=" 1.1  1.1 0.35" material="camp_wood_mat" contype="0" conaffinity="0"/>
    </body>

    <!-- Weathered Hieroglyphic Obelisks -->
    <geom name="p4_obelisk_1" type="box" size="0.25 0.25 2.10" pos="14.5 -5.8 2.10" material="obelisk_hieroglyph_mat" contype="1" conaffinity="7"/>
    <geom name="p4_obelisk_2" type="box" size="0.25 0.25 2.10" pos="19.5 -5.0 2.10" material="obelisk_hieroglyph_mat" contype="1" conaffinity="7"/>
    <geom name="p4_obelisk_3" type="box" size="0.25 0.25 2.10" pos="24.5 -14.0 2.10" material="obelisk_hieroglyph_mat" contype="1" conaffinity="7"/>

    <!-- Classical Terracotta Amphorae Urns -->
    <body name="p4_urns" pos="18.0 -5.2 0">
      <geom type="sphere" size="0.22" pos="0.5 0 0.22" material="terracotta_mat" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.10 0.12" pos="0.5 0 0.45" material="terracotta_mat" contype="0" conaffinity="0"/>
      <geom type="sphere" size="0.18" pos="-0.5 0 0.18" material="terracotta_mat" contype="1" conaffinity="7"/>
    </body>

    <!-- Saguaro & Barrel Desert Cacti -->
    <body name="p4_cactus_1" pos="12.0 -13.0 0">
      <geom type="cylinder" size="0.10 0.90" pos="0 0 0.90" material="bush_foliage_mat" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.06 0.30" pos="0.25 0 1.10" euler="1.5708 0 0" material="bush_foliage_mat" contype="0" conaffinity="0"/>
    </body>
    <body name="p4_cactus_2" pos="21.0 -14.0 0">
      <geom type="sphere" size="0.28" pos="0 0 0.28" material="bush_foliage_mat" contype="1" conaffinity="7"/>
      <geom type="sphere" size="0.04" pos="0 0 0.58" material="cactus_flower_yellow" contype="0" conaffinity="0"/>
    </body>
"""

    # ---------------------------------------------------------
    # VASTLY EXPANDED BATTERY CHARGING PLAZA
    # ---------------------------------------------------------
    xml += generate_spacious_charging_plaza_xml()

    # ---------------------------------------------------------
    # ORIGIN BASE DEPOT (HOME APRON at [0.0, -20.0])
    # ---------------------------------------------------------
    xml += f"""
    <!-- ================= ORIGIN BASE DEPOT STAGING APRON [0.0, -20.0] ================= -->
    <geom name="origin_base_pad" type="box" size="8.00 6.00 0.010" pos="{DEST_BASE[0]:.3f} {DEST_BASE[1]:.3f} 0.010" material="concrete_pad_mat" contype="0" conaffinity="0"/>
    <!-- Helipad "H" Markings -->
    <geom name="heli_ring" type="cylinder" size="2.50 0.002" pos="{DEST_BASE[0]:.3f} {DEST_BASE[1]:.3f} 0.012" material="hazard_yellow_mat" contype="0" conaffinity="0"/>
    <geom name="heli_h_left"  type="box" size="0.12 0.85 0.003" pos="{DEST_BASE[0]-0.65:.3f} {DEST_BASE[1]:.3f} 0.013" material="road_stripe_white" contype="0" conaffinity="0"/>
    <geom name="heli_h_right" type="box" size="0.12 0.85 0.003" pos="{DEST_BASE[0]+0.65:.3f} {DEST_BASE[1]:.3f} 0.013" material="road_stripe_white" contype="0" conaffinity="0"/>
    <geom name="heli_h_cross" type="box" size="0.65 0.12 0.003" pos="{DEST_BASE[0]:.3f} {DEST_BASE[1]:.3f} 0.013" material="road_stripe_white" contype="0" conaffinity="0"/>

    <!-- Shipping Containers at Base Depot -->
    <geom name="base_container_1" type="box" size="1.20 2.80 1.25" pos="-5.50 -20.0 1.25" material="container_teal" contype="1" conaffinity="7"/>
    <geom name="base_container_2" type="box" size="1.20 2.80 1.25" pos=" 5.50 -20.0 1.25" material="container_orange" contype="1" conaffinity="7"/>

    <!-- Diesel Power Generator Trailer (Staged on West Flank of Depot) -->
    <body name="base_generator_trailer" pos="-7.80 -20.0 0.45">
      <geom type="box" size="0.80 0.55 0.45" material="utility_gray_mat" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.04 0.35" pos="0.30 0 0.65" material="field_station_metal" contype="0" conaffinity="0"/>
    </body>

    <!-- Origin Telemetry Mast & Communications Dish (Staged on East Flank of Depot) -->
    <body name="origin_telemetry_mast" pos="7.80 -20.0 0">
      <geom type="cylinder" size="0.05 2.50" pos="0 0 2.50" material="field_station_metal" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.45 0.05" pos="0 0 5.10" euler="0.6 0 0" material="field_station_metal" contype="0" conaffinity="0"/>
      <geom type="sphere" size="0.10" pos="0 0 5.35" material="telemetry_beacon_blue" contype="0" conaffinity="0"/>
    </body>
"""

    # ---------------------------------------------------------
    # SMALL PATH OBSTACLES (CONES, SMALL ROCKS, BARRICADES)
    # ---------------------------------------------------------
    xml += "\n    <!-- ================= SMALL ROAD & TRANSIT CORRIDOR OBSTACLES ================= -->\n"
    for obs in SMALL_PATH_OBSTACLES:
        name = obs["name"]
        pos = obs["pos"]
        rad = obs["radius"]
        obs_type = obs["type"]

        if obs_type == "traffic_cone":
            xml += f"""    <body name="{name}" pos="{pos[0]:.2f} {pos[1]:.2f} 0">
      <geom type="cylinder" size="0.16 0.015" pos="0 0 0.015" material="traffic_cone_orange" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.10 0.16" pos="0 0 0.16" material="traffic_cone_orange" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.105 0.05" pos="0 0 0.22" material="cone_white_stripe" contype="0" conaffinity="0"/>
      <geom type="cylinder" size="0.06 0.10" pos="0 0 0.34" material="traffic_cone_orange" contype="1" conaffinity="7"/>
    </body>\n"""
        elif obs_type == "small_rock":
            xml += f"""    <body name="{name}" pos="{pos[0]:.2f} {pos[1]:.2f} 0.12">
      <geom type="mesh" mesh="small_rock_mesh" material="granite_rock_mat" contype="1" conaffinity="7" friction="2.0 0.08 0.005"/>
    </body>\n"""
        elif obs_type == "barricade":
            xml += f"""    <body name="{name}" pos="{pos[0]:.2f} {pos[1]:.2f} 0">
      <geom type="box" size="0.55 0.04 0.25" pos="0 0 0.35" material="hazard_yellow_mat" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.03 0.25" pos="-0.45 0 0.25" material="field_station_metal" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.03 0.25" pos=" 0.45 0 0.25" material="field_station_metal" contype="1" conaffinity="7"/>
    </body>\n"""
        elif obs_type == "small_stump":
            xml += f"""    <body name="{name}" pos="{pos[0]:.2f} {pos[1]:.2f} 0">
      <geom type="cylinder" size="0.25 0.18" pos="0 0 0.18" material="stump_bark_mat" contype="1" conaffinity="7"/>
      <geom type="cylinder" size="0.22 0.01" pos="0 0 0.36" material="stump_heartwood" contype="0" conaffinity="0"/>
    </body>\n"""

    # ---------------------------------------------------------
    # TRAVERSABLE OBSTACLES (ROUGH ROAD STEPS & HURDLES)
    # ---------------------------------------------------------
    for obs in TRAVERSABLE_OBSTACLES:
        name = obs["name"]
        pos = obs["pos"]
        size = obs["size"]
        e = obs["euler"]
        obs_type = obs["type"]

        if obs_type == "log_hurdle":
            xml += f"""    <body name="{name}" pos="{pos[0]:.2f} {pos[1]:.2f} {size[2]:.3f}" euler="{e[0]:.2f} {e[1]:.2f} {e[2]:.2f}">
      <geom type="cylinder" size="{size[1]:.3f} {size[0]:.2f}" euler="0 1.5708 0" material="fallen_log_mat" contype="1" conaffinity="7" friction="2.2 0.08 0.005"/>
    </body>\n"""
        elif obs_type == "broken_road_step":
            xml += f"""    <body name="{name}" pos="{pos[0]:.2f} {pos[1]:.2f} {size[2]:.3f}" euler="{e[0]:.2f} {e[1]:.2f} {e[2]:.2f}">
      <geom type="box" size="{size[0]:.2f} {size[1]:.2f} {size[2]:.3f}" material="broken_slab_mat" contype="1" conaffinity="7" friction="2.5 0.1 0.01"/>
    </body>\n"""
        elif obs_type == "bog_log":
            xml += f"""    <body name="{name}" pos="{pos[0]:.2f} {pos[1]:.2f} {size[2]:.3f}" euler="{e[0]:.2f} {e[1]:.2f} {e[2]:.2f}">
      <geom type="cylinder" size="{size[1]:.3f} {size[0]:.2f}" euler="0 1.5708 0" material="fallen_log_mat" contype="1" conaffinity="7" friction="2.6 0.12 0.008"/>
    </body>\n"""
        elif obs_type == "sand_step":
            xml += f"""    <body name="{name}" pos="{pos[0]:.2f} {pos[1]:.2f} {size[2]:.3f}" euler="{e[0]:.2f} {e[1]:.2f} {e[2]:.2f}">
      <geom type="box" size="{size[0]:.2f} {size[1]:.2f} {size[2]:.3f}" material="sandstone_mat" contype="1" conaffinity="7" friction="2.0 0.08 0.005"/>
    </body>\n"""

    # ---------------------------------------------------------
    # NON-TRAVERSABLE SITE STRUCTURE OBSTACLES (BOULDERS & STUMPS)
    # ---------------------------------------------------------
    for obs in SITE_STRUCTURE_OBSTACLES:
        name = obs["name"]
        pos = obs["pos"]
        rad = obs["radius"]
        obs_type = obs["type"]

        if obs_type == "boulder":
            xml += f"""    <body name="{name}" pos="{pos[0]:.2f} {pos[1]:.2f} {rad*0.7:.2f}">
      <geom type="sphere" size="{rad:.2f}" material="granite_rock_mat" contype="1" conaffinity="7" friction="1.8 0.05 0.002"/>
    </body>\n"""
        elif obs_type == "stump":
            xml += f"""    <body name="{name}" pos="{pos[0]:.2f} {pos[1]:.2f} 0">
      <geom type="cylinder" size="{rad:.2f} 0.50" pos="0 0 0.50" material="stump_bark_mat" contype="1" conaffinity="7"/>
    </body>\n"""

    # Add the authentic CAD robot assembly
    xml += generate_enhanced_robot_xml()

    xml += """  </worldbody>

  <actuator>
    <!-- 4 High-Torque Wheel Drive Motors -->
    <velocity name="act_wheel_FL" joint="wheel_FL_joint" kv="50" ctrlrange="-35 35"/>
    <velocity name="act_wheel_FR" joint="wheel_FR_joint" kv="50" ctrlrange="-35 35"/>
    <velocity name="act_wheel_RL" joint="wheel_RL_joint" kv="50" ctrlrange="-35 35"/>
    <velocity name="act_wheel_RR" joint="wheel_RR_joint" kv="50" ctrlrange="-35 35"/>

    <!-- 18 High-Torque RS04 Actuator Motors for 6 Articulated Legs -->
    <!-- Left Front (LF) -->
    <position name="act_LF_hip"   joint="coxa_joint_LF"  kp="350" kv="25" ctrlrange="-0.785 0.785"/>
    <position name="act_LF_femur" joint="femur_joint_LF" kp="450" kv="35" ctrlrange="-1.047 1.047"/>
    <position name="act_LF_tibia" joint="tibia_joint_LF" kp="450" kv="35" ctrlrange="-2.094 0.349"/>

    <!-- Left Mid (LM) -->
    <position name="act_LM_hip"   joint="coxa_joint_LM"  kp="350" kv="25" ctrlrange="-0.785 0.785"/>
    <position name="act_LM_femur" joint="femur_joint_LM" kp="450" kv="35" ctrlrange="-1.047 1.047"/>
    <position name="act_LM_tibia" joint="tibia_joint_LM" kp="450" kv="35" ctrlrange="-2.094 0.349"/>

    <!-- Left Rear (LR) -->
    <position name="act_LR_hip"   joint="coxa_joint_LR"  kp="350" kv="25" ctrlrange="-0.785 0.785"/>
    <position name="act_LR_femur" joint="femur_joint_LR" kp="450" kv="35" ctrlrange="-1.047 1.047"/>
    <position name="act_LR_tibia" joint="tibia_joint_LR" kp="450" kv="35" ctrlrange="-2.094 0.349"/>

    <!-- Right Front (RF) -->
    <position name="act_RF_hip"   joint="coxa_joint_RF"  kp="350" kv="25" ctrlrange="-0.785 0.785"/>
    <position name="act_RF_femur" joint="femur_joint_RF" kp="450" kv="35" ctrlrange="-1.047 1.047"/>
    <position name="act_RF_tibia" joint="tibia_joint_RF" kp="450" kv="35" ctrlrange="-2.094 0.349"/>

    <!-- Right Mid (RM) -->
    <position name="act_RM_hip"   joint="coxa_joint_RM"  kp="350" kv="25" ctrlrange="-0.785 0.785"/>
    <position name="act_RM_femur" joint="femur_joint_RM" kp="450" kv="35" ctrlrange="-1.047 1.047"/>
    <position name="act_RM_tibia" joint="tibia_joint_RM" kp="450" kv="35" ctrlrange="-2.094 0.349"/>

    <!-- Right Rear (RR) -->
    <position name="act_RR_hip"   joint="coxa_joint_RR"  kp="350" kv="25" ctrlrange="-0.785 0.785"/>
    <position name="act_RR_femur" joint="femur_joint_RR" kp="450" kv="35" ctrlrange="-1.047 1.047"/>
    <position name="act_RR_tibia" joint="tibia_joint_RR" kp="450" kv="35" ctrlrange="-2.094 0.349"/>

    <!-- Underbelly 3D LiDAR Scanning Turret Swivel -->
    <position name="act_lidar_pan" joint="lidar_pan" kp="50" kv="5" ctrlrange="-1.4 1.4"/>
  </actuator>
</mujoco>
"""

    with open(output_path, "w") as f:
        f.write(xml)
    from design_enhancements import enhance_scene
    enhance_scene(output_path)
    print(f"✅ Generated {output_path} successfully ({len(xml)} bytes)!")


if __name__ == "__main__":
    build_full_scene_xml("hybrid_hexapod_multi_place.xml")
