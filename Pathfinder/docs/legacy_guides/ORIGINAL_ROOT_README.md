The current demo adds **mild, more uneven, and blocked extreme terrain**, with
shared navigation/locomotion speed limits and eight named roads. See the
[terrain and mission guide](mujoco/README.md).

The latest MuJoCo demo has **six destinations and three charging stations** behind
one automatic Charge control, irregular physical road debris, and additional rough
terrain with automatic wheel/leg transformations. See [the current demo guide](mujoco/README.md).

# Hexapod Robot Asset for NVIDIA Isaac Lab / Isaac Sim

This standalone package contains the complete 18-DOF Hexapod robot asset exported from Autodesk Fusion 360, ready for immediate import into **NVIDIA Isaac Lab** or **Isaac Sim**.

---

## 📁 Package Contents

```text
hexapod_asset/
├── hexapod.urdf             # 18-DOF URDF with kinematics, limits, masses & foot sensors
├── hexapod_cfg.py           # Isaac Lab ArticulationCfg for direct drop-in import
├── convert_urdf_to_usd.py   # Script to convert hexapod.urdf -> hexapod.usd
├── meshes/
│   ├── base_link.stl        # Chassis / body mesh (centered at body origin)
│   ├── coxa_link.stl        # Coxa link mesh (pivot at joint origin)
│   ├── femur_link.stl       # 560 mm femur link mesh (pivot at hip joint origin)
│   ├── tibia_link.stl       # 760 mm tibia link mesh (pivot at knee joint origin)
│   └── rs04_actuator.stl    # RS04 actuator module mesh
└── README.md                # This manual
```

---

## 📥 How to Import into Isaac Lab

### Option A: Direct Python Articulation Import

Copy this `hexapod_asset` folder into your Isaac Lab project (or inside `source/extensions/omni.isaac.lab_assets/data/Robots/Hexapod`).

In your environment configuration:

```python
from hexapod_cfg import HEXAPOD_CFG

# Inside your InteractiveSceneCfg:
robot = HEXAPOD_CFG.replace(prim_path="{ENV_REGEX_NS}/Robot")
```

---

### Option B: Convert to USD (`hexapod.usd`)

Run the included converter with Isaac Lab:

```bash
# Windows
isaaclab.bat -p convert_urdf_to_usd.py

# Linux / Docker
./isaaclab.sh -p convert_urdf_to_usd.py
```

This generates `hexapod.usd` with `PhysxArticulationAPI`, drive gains ($K_p, K_d$), and contact reporters pre-configured.

---

### Option C: Import via Isaac Sim GUI

1. Open **Isaac Sim**.
2. Open menu: **Isaac Utils** -> **Workflows** -> **URDF Importer**.
3. In the URDF file browser, select `hexapod.urdf`.
4. Ensure:
   - **Fix Base Link**: unchecked (`False`)
   - **Self Collisions**: unchecked (`False`)
   - **Import Inertia Tensor**: checked (`True`)
5. Click **Import** or **Save as USD**.


## Expanded MuJoCo Route Explorer

Launch `./mujoco/run_simulation.sh` and open http://127.0.0.1:8767 . The scene has a
96 × 96 m navigation area, wide bypasses, and additional physical road obstacles.
Use **Understand the optimization** for a fixed-start distance/time/battery priority
demonstration. Permanent history records From → To, costs, arrivals and charging;
page refreshes and robot resets keep all saved records. CSV export is available.
See [`mujoco/README.md`](mujoco/README.md) for the example, storage, controls, energy
constraints and assisted-simulation scope. Original source STL/URDF files are unchanged.
