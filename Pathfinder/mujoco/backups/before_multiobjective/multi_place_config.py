"""
Multi-Place Expedition & Open-World Hub-and-Spoke Configuration (Ultra-Rich)
=============================================================================
Vastly Expanded 72m x 72m Proving Ground for Autodesk Fusion 360 CAD Hexapod:
- True Hub-and-Spoke Mission Architecture:
    * Origin: Base Depot Staging Apron [0.0, -20.0]
    * Mission Sequence:
        Origin -> Place 1 (Forest) -> Origin (Base Dwell) ->
        Origin -> Place 2 (Quarry) -> Origin (Base Dwell) ->
        Origin -> Place 3 (Marsh)  -> Origin (Base Dwell) ->
        Origin -> Place 4 (Dunes)  -> Origin (Grand Cycle Complete!)
- Shortest Collision-Free Corridors with Dedicated Small Roadside Obstacles.
- Emergency Recharge Interrupt (< 35% Battery): Diverts to Central Kiosk Pad [0.0, 1.2].
"""

import numpy as np

# ----------------------------------------------------------------------
# 1. Key Expedition Target Destinations (Meters)
# ----------------------------------------------------------------------
DEST_BASE        = np.array([0.0, -20.0], dtype=np.float32)   # Origin Base Depot Staging Apron
DEST_PLACE_1     = np.array([-18.0, 16.0], dtype=np.float32)  # Place 1: Dense Conifer Pine Forest & Camp
DEST_PLACE_2     = np.array([18.0, 16.0], dtype=np.float32)   # Place 2: Broken Granite Quarry & Ore Basin
DEST_PLACE_3     = np.array([-18.0, -10.0], dtype=np.float32) # Place 3: Churned Mud Marsh & Wetland Lagoon
DEST_PLACE_4     = np.array([18.0, -10.0], dtype=np.float32)  # Place 4: Golden Sand Dunes & Ancient Ruins
DEST_KIOSK_PAD   = np.array([0.0, 1.2], dtype=np.float32)     # Battery Charging Station Docking Pad
DEST_KIOSK_ENTRY = np.array([0.0, -4.0], dtype=np.float32)    # Front Middle Entrance to Charging Station
DEST_KIOSK       = np.array([0.0, 8.2], dtype=np.float32)     # Battery Charging Station Cabinet (14m x 18m Plaza)

# Dedicated Battery Charging Station Target (Used exclusively for low-battery recharge overrides)
KIOSK_RECHARGE_TARGET = {
    "name": "Battery Charging Station (Recharge)",
    "pos": DEST_KIOSK_PAD,
    "entry": DEST_KIOSK_ENTRY,
    "corridor": [DEST_KIOSK_ENTRY, DEST_KIOSK_PAD],
    "scan": False,
    "dwell": 7.5,
    "zone": "dock"
}

# ----------------------------------------------------------------------
# Full Interior 360° Inspection Loops (DEEPLY INSIDE EACH PLACE!)
# ----------------------------------------------------------------------
# Place 1 (Forest Camp): Verified interior loop right inside the camp clearing!
CIRCUIT_PLACE_1 = [
    {"pos": np.array([-18.0, 13.0], dtype=np.float32),  "label": "Station 1: Camp Center Clearing & Campfire Vista"},
    {"pos": np.array([-21.0, 16.0], dtype=np.float32),  "label": "Station 2: Field Science Research Tent & Sorting Station"},
    {"pos": np.array([-18.0, 20.0], dtype=np.float32),  "label": "Station 3: Central Campfire & Generator Unit"},
    {"pos": np.array([-14.5, 16.5], dtype=np.float32),  "label": "Station 4: Meteorological Tower & Woodcutting Area"},
    {"pos": np.array([-18.0, 14.5], dtype=np.float32),  "label": "Station 5: Camp Return to Central Gateway"},
]

# Place 2 (Granite Quarry): Verified interior loop right inside the excavation pit & machinery!
CIRCUIT_PLACE_2 = [
    {"pos": np.array([18.0, 13.0], dtype=np.float32),   "label": "Station 1: Quarry Excavation Pit Center & Mineral Slabs"},
    {"pos": np.array([14.5, 16.5], dtype=np.float32),   "label": "Station 2: Mining Excavator Front Clearance"},
    {"pos": np.array([18.0, 16.8], dtype=np.float32),   "label": "Station 3: Central Quarry Basin & Conveyor Incline"},
    {"pos": np.array([21.5, 16.0], dtype=np.float32),   "label": "Station 4: Site Operations Cabin & Mineral Core Trays"},
    {"pos": np.array([18.0, 12.5], dtype=np.float32),   "label": "Station 5: Quarry South Return Gateway"},
]

# Place 3 (Mud Marsh): Verified deep interior loop through wetland estuary & water pools!
CIRCUIT_PLACE_3 = [
    {"pos": np.array([-14.5, -8.0], dtype=np.float32),  "label": "Station 1: Estuary Mooring Pier & Sampling Buoy"},
    {"pos": np.array([-18.5, -10.5], dtype=np.float32), "label": "Station 2: Central Wetland Lagoon & Reed Beds"},
    {"pos": np.array([-18.5, -15.0], dtype=np.float32), "label": "Station 3: Deep Southwest Marsh & Stilt Hut Vista"},
    {"pos": np.array([-14.5, -14.0], dtype=np.float32), "label": "Station 4: Southeast Lily Bay & Hydrology Station"},
    {"pos": np.array([-14.2, -9.5], dtype=np.float32),  "label": "Station 5: Marsh Exit Gateway to Arterial Highway"},
]

# Place 4 (Sand Dunes): Verified deep interior loop through ancient desert temple ruins!
CIRCUIT_PLACE_4 = [
    {"pos": np.array([14.5, -8.0], dtype=np.float32),   "label": "Station 1: Guardian Avenue & Obelisk Vista"},
    {"pos": np.array([17.0, -7.5], dtype=np.float32),   "label": "Station 2: Sieving Station & Amphora Urns"},
    {"pos": np.array([22.5, -10.0], dtype=np.float32),  "label": "Station 3: Hypostyle Colonnade Court"},
    {"pos": np.array([19.0, -14.0], dtype=np.float32),  "label": "Station 4: Monumental Sandstone Arch Portal & Altar"},
    {"pos": np.array([14.5, -13.5], dtype=np.float32),  "label": "Station 5: Archaeologist Dig Clearing & Sunken Crypt"},
    {"pos": np.array([11.0, -13.0], dtype=np.float32),  "label": "Station 6: South Desert Apron Highway Bypass"},
    {"pos": np.array([10.5, -9.0], dtype=np.float32),   "label": "Station 7: Desert Exit Gateway Corridor"},
]

# ----------------------------------------------------------------------
# Shortest Collision-Free Corridors (Hub-and-Spoke with Alternative Routes!)
# ----------------------------------------------------------------------
# Place 1: Outbound via Western Arterial Highway, Return via Western Arterial Highway
P1_OUTBOUND = [
    DEST_BASE,                                   # [0.0, -20.0] Base Depot Apron
    np.array([0.0, -16.5], dtype=np.float32),
    np.array([0.0, -13.0], dtype=np.float32),    # Gantry Exit
    np.array([0.0, -10.0], dtype=np.float32),    # South Cross Highway Junction
    np.array([-3.5, -10.0], dtype=np.float32),
    np.array([-7.0, -10.0], dtype=np.float32),
    np.array([-10.0, -10.0], dtype=np.float32),  # West Highway South
    np.array([-10.0, -6.5], dtype=np.float32),
    np.array([-10.0, -3.0], dtype=np.float32),
    np.array([-10.0, 0.0], dtype=np.float32),    # West Highway Mid
    np.array([-10.0, 3.5], dtype=np.float32),
    np.array([-10.0, 7.0], dtype=np.float32),
    np.array([-10.0, 10.5], dtype=np.float32),
    np.array([-10.0, 14.0], dtype=np.float32),
    np.array([-10.0, 16.0], dtype=np.float32),   # Northwest Junction
    np.array([-14.0, 16.0], dtype=np.float32),   # Forest Camp Approach
    DEST_PLACE_1,                                # [-18.0, 16.0] Forest Camp Gateway
]

P1_RETURN = [
    DEST_PLACE_1,                                # [-18.0, 16.0] Forest Camp Gateway
    np.array([-14.0, 16.0], dtype=np.float32),   # Forest Camp Exit Trail
    np.array([-10.0, 16.0], dtype=np.float32),   # Northwest Junction back to Highway
    np.array([-10.0, 13.5], dtype=np.float32),
    np.array([-10.0, 11.0], dtype=np.float32),
    np.array([-10.0, 8.5], dtype=np.float32),
    np.array([-10.0, 6.0], dtype=np.float32),
    np.array([-10.0, 3.5], dtype=np.float32),
    np.array([-10.0, 1.0], dtype=np.float32),
    np.array([-10.0, -1.5], dtype=np.float32),
    np.array([-10.0, -4.5], dtype=np.float32),
    np.array([-10.0, -7.5], dtype=np.float32),
    np.array([-10.0, -10.0], dtype=np.float32),  # West Highway South
    np.array([-7.0, -10.0], dtype=np.float32),
    np.array([-3.5, -10.0], dtype=np.float32),
    np.array([0.0, -10.0], dtype=np.float32),    # South Cross Bypass
    np.array([0.0, -13.0], dtype=np.float32),    # Apron Inbound Channel
    np.array([0.0, -16.5], dtype=np.float32),
    DEST_BASE,
]

# Place 2: Outbound via Eastern Arterial Highway, Return via Eastern Arterial Highway
P2_OUTBOUND = [
    DEST_BASE,
    np.array([0.0, -16.5], dtype=np.float32),
    np.array([0.0, -13.0], dtype=np.float32),    # Gantry Exit
    np.array([0.0, -10.0], dtype=np.float32),    # South Cross Highway Junction
    np.array([3.5, -10.0], dtype=np.float32),
    np.array([7.0, -10.0], dtype=np.float32),
    np.array([10.0, -10.0], dtype=np.float32),   # East Highway South
    np.array([10.0, -6.5], dtype=np.float32),
    np.array([10.0, -3.0], dtype=np.float32),
    np.array([10.0, 0.0], dtype=np.float32),     # East Highway Mid
    np.array([10.0, 3.5], dtype=np.float32),
    np.array([10.0, 7.0], dtype=np.float32),
    np.array([10.0, 10.5], dtype=np.float32),
    np.array([10.0, 14.0], dtype=np.float32),
    np.array([10.0, 16.0], dtype=np.float32),    # Northeast Junction
    np.array([14.0, 16.0], dtype=np.float32),    # Quarry Approach
    DEST_PLACE_2,                                # [18.0, 16.0] Quarry Gateway
]

P2_RETURN = [
    DEST_PLACE_2,                                # [18.0, 16.0] Quarry Gateway
    np.array([14.0, 16.0], dtype=np.float32),    # Quarry Exit Trail
    np.array([10.0, 16.0], dtype=np.float32),    # Northeast Junction back to Highway
    np.array([10.0, 13.5], dtype=np.float32),
    np.array([10.0, 11.0], dtype=np.float32),
    np.array([10.0, 8.5], dtype=np.float32),
    np.array([10.0, 6.0], dtype=np.float32),
    np.array([10.0, 3.5], dtype=np.float32),
    np.array([10.0, 1.0], dtype=np.float32),
    np.array([10.0, -1.5], dtype=np.float32),
    np.array([10.0, -4.5], dtype=np.float32),
    np.array([10.0, -7.5], dtype=np.float32),
    np.array([10.0, -10.0], dtype=np.float32),   # East Highway South
    np.array([7.0, -10.0], dtype=np.float32),
    np.array([3.5, -10.0], dtype=np.float32),
    np.array([0.0, -10.0], dtype=np.float32),    # South Cross Bypass
    np.array([0.0, -13.0], dtype=np.float32),    # Apron Inbound Channel
    np.array([0.0, -16.5], dtype=np.float32),
    DEST_BASE,
]

# Place 3: Outbound via North Lagoon Trail, Return via South Marsh Levee
P3_OUTBOUND = [
    DEST_BASE,
    np.array([0.0, -16.5], dtype=np.float32),
    np.array([0.0, -13.0], dtype=np.float32),    # Gantry Exit
    np.array([0.0, -10.0], dtype=np.float32),    # South Cross Highway Junction
    np.array([-4.0, -10.0], dtype=np.float32),
    np.array([-8.0, -10.0], dtype=np.float32),   # Westbound Arterial
    np.array([-11.0, -9.0], dtype=np.float32),
    np.array([-13.0, -8.0], dtype=np.float32),   # Lagoon Estuary Waypoint
    DEST_PLACE_3,
]

P3_RETURN = [
    np.array([-14.2, -9.5], dtype=np.float32),   # Marsh North Exit
    np.array([-12.0, -10.0], dtype=np.float32),
    np.array([-9.0, -10.0], dtype=np.float32),   # South Marsh Levee
    np.array([-5.0, -10.0], dtype=np.float32),
    np.array([0.0, -10.0], dtype=np.float32),    # South Cross Highway Return
    np.array([0.0, -13.0], dtype=np.float32),    # Apron Inbound Channel
    np.array([0.0, -16.5], dtype=np.float32),
    DEST_BASE,
]

# Place 4: Outbound via Oasis Track, Return via Ancient Colonnade Trail
P4_OUTBOUND = [
    DEST_BASE,
    np.array([0.0, -16.5], dtype=np.float32),
    np.array([0.0, -13.0], dtype=np.float32),    # Gantry Exit
    np.array([0.0, -10.0], dtype=np.float32),    # South Cross Highway Junction
    np.array([4.0, -10.0], dtype=np.float32),
    np.array([8.0, -10.0], dtype=np.float32),    # Eastbound Arterial
    np.array([11.0, -9.0], dtype=np.float32),
    np.array([13.0, -8.0], dtype=np.float32),    # Dune Crest Waypoint
    DEST_PLACE_4,
]

P4_RETURN = [
    np.array([14.2, -9.5], dtype=np.float32),    # Ruins North Exit
    np.array([12.0, -10.0], dtype=np.float32),
    np.array([9.0, -10.0], dtype=np.float32),    # Colonnade South Trail
    np.array([5.0, -10.0], dtype=np.float32),
    np.array([0.0, -10.0], dtype=np.float32),    # South Cross Highway Return
    np.array([0.0, -13.0], dtype=np.float32),    # Apron Inbound Channel
    np.array([0.0, -16.5], dtype=np.float32),
    DEST_BASE,
]

# ----------------------------------------------------------------------
# Grand Hub-and-Spoke Mission Sequence (Origin -> Site -> Origin -> Site)
# ----------------------------------------------------------------------
MISSION_TARGETS = [
    # Mission Leg 1: Origin -> Place 1 (Pine Forest) -> Origin
    {
        "name": "Place 1 (Pine Forest)",
        "pos": DEST_PLACE_1,
        "approach": P1_OUTBOUND,
        "circuit": CIRCUIT_PLACE_1,
        "return_corridor": P1_RETURN,
        "scan": True,
        "zone": "forest"
    },

    # Mission Leg 2: Origin -> Place 2 (Granite Quarry) -> Origin
    {
        "name": "Place 2 (Rocky Quarry)",
        "pos": DEST_PLACE_2,
        "approach": P2_OUTBOUND,
        "circuit": CIRCUIT_PLACE_2,
        "return_corridor": P2_RETURN,
        "scan": True,
        "zone": "rocky"
    },

    # Mission Leg 3: Origin -> Place 3 (Mud Marsh) -> Origin
    {
        "name": "Place 3 (Mud Marsh)",
        "pos": DEST_PLACE_3,
        "approach": P3_OUTBOUND,
        "circuit": CIRCUIT_PLACE_3,
        "return_corridor": P3_RETURN,
        "scan": True,
        "zone": "mud"
    },

    # Mission Leg 4: Origin -> Place 4 (Desert Ruins) -> Origin
    {
        "name": "Place 4 (Sand Clearing)",
        "pos": DEST_PLACE_4,
        "approach": P4_OUTBOUND,
        "circuit": CIRCUIT_PLACE_4,
        "return_corridor": P4_RETURN,
        "scan": True,
        "zone": "sand"
    },
]

def get_kiosk_departure_corridor(target_idx):
    """
    Returns an obstacle-free departure corridor from the Battery Charging Station Pad [0.0, 1.2]
    out to the requested expedition target destination without colliding with any kiosk structures.
    Always exits south via DEST_KIOSK_ENTRY [0.0, -4.0] before turning onto lateral arterial bypass highways!
    """
    if target_idx == 0:
        # Place 1: Dense Pine Forest (North-West)
        return [
            DEST_KIOSK_ENTRY,
            np.array([-4.0, -4.0], dtype=np.float32),
            np.array([-7.0, -4.0], dtype=np.float32),
            np.array([-10.0, -4.0], dtype=np.float32),
            np.array([-10.0, -1.0], dtype=np.float32),
            np.array([-10.0, 2.5], dtype=np.float32),
            np.array([-10.0, 6.0], dtype=np.float32),
            np.array([-10.0, 9.5], dtype=np.float32),
            np.array([-10.0, 13.0], dtype=np.float32),
            np.array([-10.0, 16.0], dtype=np.float32),
            np.array([-14.0, 16.0], dtype=np.float32),
            DEST_PLACE_1,
        ]
    elif target_idx == 1:
        # Place 2: Broken Granite Quarry (North-East)
        return [
            DEST_KIOSK_ENTRY,
            np.array([4.0, -4.0], dtype=np.float32),
            np.array([7.0, -4.0], dtype=np.float32),
            np.array([10.0, -4.0], dtype=np.float32),
            np.array([10.0, -1.0], dtype=np.float32),
            np.array([10.0, 2.5], dtype=np.float32),
            np.array([10.0, 6.0], dtype=np.float32),
            np.array([10.0, 9.5], dtype=np.float32),
            np.array([10.0, 13.0], dtype=np.float32),
            np.array([10.0, 16.0], dtype=np.float32),
            np.array([14.0, 16.0], dtype=np.float32),
            DEST_PLACE_2,
        ]
    elif target_idx == 2:
        # Place 3: Wet Mud Marsh (South-West)
        return [
            DEST_KIOSK_ENTRY,
            np.array([0.0, -7.0], dtype=np.float32),
            np.array([0.0, -10.0], dtype=np.float32),
            np.array([-4.0, -10.0], dtype=np.float32),
            np.array([-8.0, -10.0], dtype=np.float32),
            np.array([-11.0, -9.0], dtype=np.float32),
            np.array([-13.0, -8.0], dtype=np.float32),
            DEST_PLACE_3,
        ]
    elif target_idx == 3:
        # Place 4: Golden Sand Dunes (South-East)
        return [
            DEST_KIOSK_ENTRY,
            np.array([0.0, -7.0], dtype=np.float32),
            np.array([0.0, -10.0], dtype=np.float32),
            np.array([4.0, -10.0], dtype=np.float32),
            np.array([8.0, -10.0], dtype=np.float32),
            np.array([11.0, -9.0], dtype=np.float32),
            np.array([13.0, -8.0], dtype=np.float32),
            DEST_PLACE_4,
        ]
    else:
        # Direct return to Origin Base Depot Staging Apron [0.0, -20.0]
        return [
            DEST_KIOSK_ENTRY,
            np.array([0.0, -7.0], dtype=np.float32),
            np.array([0.0, -10.0], dtype=np.float32),
            np.array([0.0, -13.0], dtype=np.float32),
            np.array([0.0, -16.5], dtype=np.float32),
            DEST_BASE,
        ]

def get_kiosk_approach_corridor(curr_pos):
    """
    Returns an obstacle-free corridor from any field position in the 72m world
    to enter the Battery Charging Station Pad [0.0, 1.2] strictly via front middle entry [0.0, -4.0].
    """
    x, y = float(curr_pos[0]), float(curr_pos[1])
    corridor = []

    if y > 2.0:
        # North of kiosk: Route south along west or east highway down to y = -4.0
        side_x = -10.0 if x < 0 else 10.0
        if abs(x) > 11.5:
            corridor.append(np.array([side_x, 16.0], dtype=np.float32))

        # Dense highway waypoints heading south towards y = -4.0
        for y_step in np.arange(min(y, 16.0), -4.1, -3.0):
            corridor.append(np.array([side_x, float(y_step)], dtype=np.float32))
        corridor.append(np.array([side_x, -4.0], dtype=np.float32))
        corridor.append(np.array([side_x * 0.5, -4.0], dtype=np.float32))
        corridor.append(DEST_KIOSK_ENTRY)
    elif y < -6.0:
        # South of kiosk: Route up the central highway
        for y_step in np.arange(y, -4.1, 3.0):
            corridor.append(np.array([0.0, float(y_step)], dtype=np.float32))
        corridor.append(DEST_KIOSK_ENTRY)
    else:
        # Mid-latitude approach (y in [-6.0, 2.0])
        if abs(x) > 3.0:
            side_x = -10.0 if x < 0 else 10.0
            corridor.append(np.array([side_x, -4.0], dtype=np.float32))
            corridor.append(np.array([side_x * 0.5, -4.0], dtype=np.float32))
        corridor.append(DEST_KIOSK_ENTRY)

    corridor.append(DEST_KIOSK_PAD)
    return corridor

# ----------------------------------------------------------------------
# 2. Zone Bounding Boxes for Terrain Classification [xmin, xmax, ymin, ymax]
# ----------------------------------------------------------------------
ZONE_BBOX_MUD    = [-26.0, -12.0, -18.0, -6.0]   # Mud Marsh Floor & Wetland Lagoon
ZONE_BBOX_ROCKY  = [12.0, 26.0, 9.0, 24.0]        # Granite Quarry Basin & Broken Slabs
ZONE_BBOX_FOREST = [-26.0, -12.0, 9.0, 24.0]      # Alpine Pine Forest & Science Camp
ZONE_BBOX_SAND   = [12.0, 26.0, -18.0, -6.0]      # Golden Desert Sand Dunes & Ancient Ruins

# ----------------------------------------------------------------------
# 3. NON-TRAVERSABLE SITE STRUCTURES (High landmarks to steer around)
# ----------------------------------------------------------------------
SITE_STRUCTURE_OBSTACLES = [
    # Honda e:TECHNOLOGY Battery Swap Kiosk (Open-Air Design matching Reference Image)
    {"name": "kiosk_tower",     "pos": np.array([0.0, 8.2]),     "radius": 0.70, "type": "kiosk"},
    {"name": "kiosk_bollard_l", "pos": np.array([-3.5, 2.0]),    "radius": 0.20, "type": "pillar"},
    {"name": "kiosk_bollard_r", "pos": np.array([3.5, 2.0]),     "radius": 0.20, "type": "pillar"},

    # Base Depot Entrance Gantry Posts [x = ±3.6, y = -14.0] (flanking central 7m highway)
    {"name": "gantry_post_sw",  "pos": np.array([-3.6, -14.0]),  "radius": 0.25, "type": "pillar"},
    {"name": "gantry_post_se",  "pos": np.array([3.6, -14.0]),   "radius": 0.25, "type": "pillar"},

    # Base Depot Staging Structures (Flanking Apron)
    {"name": "base_cont_1",     "pos": np.array([-5.5, -20.0]),  "radius": 1.40, "type": "container"},
    {"name": "base_cont_2",     "pos": np.array([5.5, -20.0]),   "radius": 1.40, "type": "container"},
    {"name": "base_gen",        "pos": np.array([-7.8, -20.0]),  "radius": 0.60, "type": "generator"},
    {"name": "base_mast",       "pos": np.array([7.8, -20.0]),   "radius": 0.40, "type": "mast"},

    # Central Open Ground Boulders & Stumps (well clear of highways)
    {"name": "boulder_c1",      "pos": np.array([-5.0, -7.0]),   "radius": 0.55, "type": "boulder"},
    {"name": "boulder_c2",      "pos": np.array([5.0, -7.0]),    "radius": 0.55, "type": "boulder"},
    {"name": "stump_c3",        "pos": np.array([-1.8, -6.5]),   "radius": 0.45, "type": "stump"},
    {"name": "stump_c4",        "pos": np.array([1.8, -6.5]),    "radius": 0.45, "type": "stump"},
    {"name": "boulder_c5",      "pos": np.array([7.5, 14.0]),    "radius": 0.55, "type": "boulder"},

    # Place 1 (Forest Camp) Structures
    {"name": "p1_tent",         "pos": np.array([-24.0, 16.0]),  "radius": 1.20, "type": "camp"},
    {"name": "p1_desk",         "pos": np.array([-22.5, 18.0]),  "radius": 0.50, "type": "camp"},
    {"name": "p1_generator",    "pos": np.array([-20.5, 22.0]),  "radius": 0.65, "type": "camp"},
    {"name": "p1_weather_mast", "pos": np.array([-13.0, 19.0]),  "radius": 0.35, "type": "camp"},
    {"name": "p1_woodcutting",  "pos": np.array([-13.0, 11.0]),  "radius": 0.70, "type": "camp"},
    {"name": "p1_watchtower",   "pos": np.array([-26.0, 22.0]),  "radius": 1.50, "type": "camp"},
    {"name": "p1_cabin",        "pos": np.array([-25.0, 13.0]),  "radius": 1.50, "type": "camp"},

    # Place 2 (Quarry) Structures
    {"name": "p2_cairn",        "pos": np.array([24.0, 20.0]),   "radius": 0.75, "type": "quarry"},
    {"name": "p2_crane",        "pos": np.array([20.5, 22.0]),   "radius": 1.00, "type": "quarry"},
    {"name": "p2_conveyor",     "pos": np.array([23.0, 17.5]),   "radius": 0.90, "type": "quarry"},
    {"name": "p2_drill_rig",    "pos": np.array([12.5, 19.5]),   "radius": 0.85, "type": "quarry"},
    {"name": "p2_site_office",  "pos": np.array([25.0, 13.0]),   "radius": 1.50, "type": "quarry"},
    {"name": "p2_excavator_cab",    "pos": np.array([15.0, 21.0]),   "radius": 1.45, "type": "quarry"},
    {"name": "p2_excavator_bucket", "pos": np.array([17.8, 19.8]),   "radius": 1.25, "type": "quarry"},
    {"name": "p2_stone_pallets","pos": np.array([21.0, 11.0]),   "radius": 0.65, "type": "quarry"},

    # Place 3 (Marsh) Structures
    {"name": "p3_pier",         "pos": np.array([-12.5, -6.0]),  "radius": 0.60, "type": "marsh"},
    {"name": "p3_weather_buoy", "pos": np.array([-12.0, -12.0]), "radius": 0.35, "type": "marsh"},
    {"name": "p3_stilt_platform","pos": np.array([-24.0, -15.0]),"radius": 1.20, "type": "marsh"},

    # Place 4 (Desert) Structures
    {"name": "p4_arch_L",       "pos": np.array([17.5, -16.0]),  "radius": 0.45, "type": "desert"},
    {"name": "p4_arch_R",       "pos": np.array([21.5, -16.0]),  "radius": 0.45, "type": "desert"},
    {"name": "p4_guardian_1",   "pos": np.array([12.5, -5.5]),   "radius": 0.45, "type": "desert"},
    {"name": "p4_guardian_2",   "pos": np.array([13.0, -11.0]),  "radius": 0.45, "type": "desert"},
    {"name": "p4_temple_stairs","pos": np.array([19.0, -16.5]),  "radius": 0.75, "type": "desert"},
    {"name": "p4_colonnade",    "pos": np.array([25.0, -10.0]),  "radius": 1.00, "type": "desert"},
    {"name": "p4_khaki_tent",   "pos": np.array([21.0, -6.5]),   "radius": 1.00, "type": "desert"},
    {"name": "p4_sieving_station","pos": np.array([17.0, -4.5]), "radius": 0.60, "type": "desert"},
    {"name": "p4_ancient_obelisk","pos": np.array([25.0, -14.5]),"radius": 1.00, "type": "desert"},
    {"name": "p4_hoodoo_2",     "pos": np.array([22.5, -13.0]),  "radius": 0.65, "type": "desert"},
]

# ----------------------------------------------------------------------
# 4. SMALL ROAD & TRANSIT CORRIDOR OBSTACLES (Cones, Small Rocks, Barricades)
# ----------------------------------------------------------------------
SMALL_PATH_OBSTACLES = [
    # ------------------------------------------------------------------
    # ACTIVE ROADWAY OBSTACLES (ON-ROAD CONES, SMALL ROCKS, BARRICADES)
    # Placed on road lanes for dynamic autonomous evasion with zero collision!
    # ------------------------------------------------------------------
    # West Arterial Highway (x = -10.0, Connecting Place 1 & Place 3)
    {"name": "cone_road_w1", "pos": np.array([-10.40, -3.5]), "radius": 0.20, "type": "traffic_cone"},
    {"name": "rock_road_w1", "pos": np.array([ -9.60,  2.5]), "radius": 0.24, "type": "small_rock"},
    {"name": "cone_road_w2", "pos": np.array([-10.40,  7.5]), "radius": 0.20, "type": "traffic_cone"},
    {"name": "rock_road_w2", "pos": np.array([ -9.60, -7.0]), "radius": 0.24, "type": "small_rock"},
    {"name": "cone_road_w3", "pos": np.array([-10.35,  4.5]), "radius": 0.20, "type": "traffic_cone"},
    {"name": "barr_road_w1", "pos": np.array([ -9.55, 11.5]), "radius": 0.30, "type": "barricade"},

    # East Arterial Highway (x = +10.0, Connecting Place 2 & Place 4)
    {"name": "cone_road_e1", "pos": np.array([ 10.40, -3.5]), "radius": 0.20, "type": "traffic_cone"},
    {"name": "rock_road_e1", "pos": np.array([  9.60,  2.5]), "radius": 0.24, "type": "small_rock"},
    {"name": "cone_road_e2", "pos": np.array([ 10.40,  7.5]), "radius": 0.20, "type": "traffic_cone"},
    {"name": "rock_road_e2", "pos": np.array([  9.60, -7.0]), "radius": 0.24, "type": "small_rock"},
    {"name": "cone_road_e3", "pos": np.array([ 10.35,  4.5]), "radius": 0.20, "type": "traffic_cone"},
    {"name": "barr_road_e1", "pos": np.array([  9.55, 11.5]), "radius": 0.30, "type": "barricade"},

    # South Cross Highway (y = -10.0, East-West Connector)
    {"name": "rock_road_s1", "pos": np.array([ -5.00, -9.65]), "radius": 0.24, "type": "small_rock"},
    {"name": "cone_road_s1", "pos": np.array([  5.00, -10.35]), "radius": 0.20, "type": "traffic_cone"},
    {"name": "cone_road_s2", "pos": np.array([ -2.50, -10.35]), "radius": 0.20, "type": "traffic_cone"},
    {"name": "rock_road_s2", "pos": np.array([  2.50, -9.65]), "radius": 0.24, "type": "small_rock"},

    # North Cross Highway (y = +16.0, Connecting Place 1 & Place 2)
    {"name": "cone_road_n1", "pos": np.array([ -5.00, 16.35]), "radius": 0.20, "type": "traffic_cone"},
    {"name": "rock_road_n1", "pos": np.array([  5.00, 15.65]), "radius": 0.24, "type": "small_rock"},
    {"name": "barr_road_n1", "pos": np.array([  0.00, 16.35]), "radius": 0.28, "type": "barricade"},

    # Central Inbound Highway (x = 0.0, Base Depot Approach)
    {"name": "cone_road_c1", "pos": np.array([ -0.45, -15.0]), "radius": 0.20, "type": "traffic_cone"},
    {"name": "rock_road_c1", "pos": np.array([  0.45,  -7.0]), "radius": 0.24, "type": "small_rock"},
    {"name": "cone_road_c2", "pos": np.array([  0.45, -17.5]), "radius": 0.20, "type": "traffic_cone"},
    {"name": "rock_road_c2", "pos": np.array([ -0.45, -12.0]), "radius": 0.24, "type": "small_rock"},

    # Site Approach Road Entries
    {"name": "cone_p1_entry", "pos": np.array([-13.5, 16.35]), "radius": 0.20, "type": "traffic_cone"},
    {"name": "cone_p2_entry", "pos": np.array([ 13.5, 16.35]), "radius": 0.20, "type": "traffic_cone"},
    {"name": "cone_p3_entry", "pos": np.array([-11.0, -9.65]), "radius": 0.20, "type": "traffic_cone"},
    {"name": "cone_p4_entry", "pos": np.array([ 11.0, -9.65]), "radius": 0.20, "type": "traffic_cone"},

    # ------------------------------------------------------------------
    # ROADSIDE WARNING MARKERS & VERGE HAZARDS
    # ------------------------------------------------------------------
    {"name": "cone_p1_1",   "pos": np.array([-6.0, -17.0]),  "radius": 0.18, "type": "traffic_cone"},
    {"name": "cone_p1_2",   "pos": np.array([-12.5, 2.0]),   "radius": 0.18, "type": "traffic_cone"},
    {"name": "cone_p1_3",   "pos": np.array([-12.5, 10.0]),  "radius": 0.18, "type": "traffic_cone"},

    {"name": "cone_p2_1",   "pos": np.array([6.0, -17.0]),   "radius": 0.18, "type": "traffic_cone"},
    {"name": "cone_p2_2",   "pos": np.array([12.5, 2.0]),    "radius": 0.18, "type": "traffic_cone"},
    {"name": "cone_p2_3",   "pos": np.array([12.5, 8.5]),    "radius": 0.18, "type": "traffic_cone"},

    {"name": "cone_p3_1",   "pos": np.array([-6.0, -18.5]),  "radius": 0.18, "type": "traffic_cone"},
    {"name": "cone_p3_2",   "pos": np.array([-8.5, -14.5]),  "radius": 0.18, "type": "traffic_cone"},

    {"name": "cone_p4_1",   "pos": np.array([6.0, -18.5]),   "radius": 0.18, "type": "traffic_cone"},
    {"name": "cone_p4_2",   "pos": np.array([8.5, -14.5]),   "radius": 0.18, "type": "traffic_cone"},

    {"name": "rock_p1_1",   "pos": np.array([-12.5, -2.0]),  "radius": 0.28, "type": "small_rock"},
    {"name": "rock_p2_1",   "pos": np.array([12.5, -2.0]),   "radius": 0.28, "type": "small_rock"},
    {"name": "rock_p3_1",   "pos": np.array([-12.5, -13.5]), "radius": 0.26, "type": "small_rock"},
    {"name": "rock_p4_1",   "pos": np.array([10.0, -15.5]),  "radius": 0.26, "type": "small_rock"},

    {"name": "barr_p1_1",   "pos": np.array([-12.5, 7.0]),   "radius": 0.32, "type": "barricade"},
    {"name": "barr_p2_1",   "pos": np.array([12.5, 7.0]),    "radius": 0.32, "type": "barricade"},

    {"name": "stump_p1_1",  "pos": np.array([-12.5, 12.0]),  "radius": 0.28, "type": "small_stump"},
]

# Combined non-traversable obstacle list for predictive radar & potential field avoidance
NON_TRAVERSABLE_OBSTACLES = SITE_STRUCTURE_OBSTACLES + SMALL_PATH_OBSTACLES
OPEN_WORLD_OBSTACLES = NON_TRAVERSABLE_OBSTACLES
SKETCH_OBSTACLES = OPEN_WORLD_OBSTACLES

# ----------------------------------------------------------------------
# 5. TRAVERSABLE OBSTACLES & ROUGH ROAD BREAKS (STEP OVER WITH 6 LEGS!)
# ----------------------------------------------------------------------
TRAVERSABLE_OBSTACLES = [
    # Place 1 (Forest): Fallen Pine Log Hurdles
    {
        "name": "forest_hurdle_1",
        "pos": np.array([-18.0, 10.5], dtype=np.float32),
        "size": np.array([1.8, 0.050, 0.025], dtype=np.float32),
        "euler": [0, 0, 0.05],
        "type": "log_hurdle",
        "label": "Fallen Timber Hurdle (Forest Trail)"
    },
    # Place 2 (Quarry): Broken Road Fractured Rock Steps
    {
        "name": "quarry_step_1",
        "pos": np.array([15.5, 10.5], dtype=np.float32),
        "size": np.array([1.6, 0.75, 0.025], dtype=np.float32),
        "euler": [0.03, -0.02, 0.42],
        "type": "broken_road_step",
        "label": "Broken Stone Road Step (Quarry Entry)"
    },
    # Place 3 (Mud Marsh): Sunken Bog Logs
    {
        "name": "bog_log_1",
        "pos": np.array([-12.5, -9.5], dtype=np.float32),
        "size": np.array([1.8, 0.050, 0.025], dtype=np.float32),
        "euler": [0, 0, 0.62],
        "type": "bog_log",
        "label": "Sunken Bog Timber Crossing (Mud Marsh Entry)"
    },
    # Place 4 (Sand Clearing): Low Sandstone Step
    {
        "name": "sand_step_1",
        "pos": np.array([13.5, -8.0], dtype=np.float32),
        "size": np.array([1.8, 0.70, 0.030], dtype=np.float32),
        "euler": [0.02, -0.02, 0.25],
        "type": "sand_step",
        "label": "Low Sandstone Shelf (Dune Entry)"
    },
]
