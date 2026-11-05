# Current walking-only validation

- Full tour: 72,545 control frames / 1,160.72 simulated seconds; all four places, all 22 scan sectors, return to base, and two charging cycles completed.
- Desert scan interruption and charging return: 19,000 frames / 304 simulated seconds; charging completed and scan resumed.
- Both runs: zero obstacle contacts, obstacle penetrations, navigation failures, safety holds, or MuJoCo solver warnings; all state values finite.
- Full-tour maximum body tilt: approximately 0.90 degrees.
- Invisible source foot collision spheres exhibit up to approximately 4.2 mm ground-contact compliance. Ground support contacts are excluded from obstacle contacts.
- Geometry audit: 20 source mesh visuals plus 18 instances of the authorized actuator replacement. No wheels or other added robot visual geometry.
- Missing actuator replacement correctly raises MissingAssetError.

These results cover assisted chassis stabilization, ideal limb gravity compensation, and the configured static scene. They do not establish hardware balance or torque feasibility.
See the JSON reports and walking_validation_manifest.json for detailed values and source hashes.
