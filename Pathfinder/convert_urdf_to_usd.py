"""
Convert Hexapod URDF to USD for Isaac Lab / Isaac Sim
=====================================================
Usage:
    # Run with Isaac Lab python executable:
    isaaclab.bat -p convert_urdf_to_usd.py
    # Or in Linux / Docker:
    ./isaaclab.sh -p convert_urdf_to_usd.py
"""

import argparse
import os
import sys

from omni.isaac.kit import SimulationApp

simulation_app = SimulationApp({"headless": True})

import omni.kit.commands
from omni.isaac.core.utils.extensions import enable_extension
from pxr import PhysxSchema, Usd

enable_extension("omni.isaac.urdf")


def convert(urdf_path: str, usd_path: str):
    print(f"=== Converting Hexapod URDF to USD ===")
    print(f"URDF Source: {urdf_path}")
    print(f"USD Output:  {usd_path}")

    status, import_config = omni.kit.commands.execute("URDFCreateImportConfig")
    import_config.merge_fixed_joints = False
    import_config.convex_decomp = False
    import_config.import_inertia_tensor = True
    import_config.fix_base = False
    import_config.make_default_prim = True
    import_config.self_collision = False
    import_config.create_physics_scene = True
    import_config.distance_scale = 1.0
    import_config.density = 0.0

    omni.kit.commands.execute(
        "URDFParseAndImportFile",
        urdf_path=urdf_path,
        import_config=import_config,
        dest_path=usd_path,
    )

    stage = Usd.Stage.Open(usd_path)
    if not stage:
        raise RuntimeError(f"Failed to open USD stage at: {usd_path}")

    root_prim = stage.GetDefaultPrim()
    if not root_prim:
        root_prim = stage.GetPrimAtPath("/hexapod")

    if not root_prim.HasAPI(PhysxSchema.PhysxArticulationAPI):
        PhysxSchema.PhysxArticulationAPI.Apply(root_prim)
    art_api = PhysxSchema.PhysxArticulationAPI(root_prim)
    art_api.CreateSolverPositionIterationCountAttr(8)
    art_api.CreateSolverVelocityIterationCountAttr(2)
    art_api.CreateEnabledSelfCollisionsAttr(False)

    stage.GetRootLayer().Save()
    print(f"Successfully generated: {usd_path}")


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    urdf = os.path.join(current_dir, "hexapod.urdf")
    usd = os.path.join(current_dir, "hexapod.usd")
    convert(urdf, usd)
    simulation_app.close()
