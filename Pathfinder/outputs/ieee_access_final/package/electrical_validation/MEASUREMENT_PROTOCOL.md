# Electrical battery validation still requires real measurements

No sensor values or fitted coefficients are supplied in this package.

1. Record synchronized voltage, discharge current and timestamps from the robot battery while it follows a mission. Record actual odometry distance and accumulated absolute turning. Exclude charging/service periods. State whether all robot electronics are inside the measurement boundary.
2. Fill mission_metadata.json with the real instrument, mission/map identifiers, measured distance/turning and calibration or validation split. Use raw_voltage_current.csv for the real samples; positive current means discharge.
3. Run: python3 -m research.electrical_logging --samples raw_voltage_current.csv --metadata mission_metadata.json --out integrated_mission.json
4. Put each integrated observation into electrical_measurements.csv using its existing header. Keep missions and maps disjoint between calibration and validation. The current four-coefficient model requires varied distance, duration and turning: at least 12 calibration and 6 validation observations, at least three missions per split, and a full-rank design.
5. Fill metadata.json with measured usable battery capacity in Wh and sensor details. Run: python3 -m research.calibration --csv electrical_measurements.csv --metadata metadata.json --out fitted_profile.json
6. Inspect held-out error, residuals versus time/terrain/payload, sensor uncertainty and coefficient stability before applying the profile. Independent hardware review is required. Refit only on the calibration split; evaluate changes on new held-out missions. Mechanical actuator work and simulated battery ledgers cannot replace electrical measurements.
