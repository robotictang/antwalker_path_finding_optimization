import numpy as np
from multi_place_config import DEST_KIOSK_ENTRY, DEST_KIOSK_PAD

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
