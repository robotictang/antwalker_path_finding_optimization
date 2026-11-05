# Research reference review

Reviewed 27 October 2026. Scope: the four identifiable papers discussed in the uploaded `name.docx`. This is a targeted review, not an exhaustive review of the field. Three full texts were accessible; the CASE paper was reviewed only through its publisher abstract/introduction and DOI metadata. Local PDFs are retained for research inspection, not included in a publicly hosted dashboard.

## Smart Gait

Yin, Gao, Sun, Zhao and Xiao. *Smart Gait: A Gait Optimization Framework for Hexapod Robots*. Chinese Journal of Mechanical Engineering 37, article 15 (2024). [Version of record](https://doi.org/10.1186/s10033-024-01000-0). Full paper reviewed, with the accessible 2023 preprint cross-checked.

The framework combines offline swing-trajectory and period/duty optimization with an online leg-lifting adapter and whole-body control. A two-segment fourth-order Bézier swing trajectory is optimized using leg dynamics; support forces and torque constraints enter timing optimization. Its 15.9% result refers to the paper's period/duty experiment, not a guaranteed battery saving here. The paper calls that comparison average joint power, while Figure 13 labels the trace average torque squared; preserve this metric qualification when citing it.

**Feasible adaptation:** expose gait period, duty, lift and trajectory parameters, run a matched sweep, and log positive actuator mechanical work, torque-squared effort, body tilt and foot contact. This is **Smart-Gait-inspired parameter tuning**, not reproduction of its dynamics optimization, support-force QP, online adapter or whole-body controller. Do not substitute distance-based battery drain for a gait-effort measurement.

## Multi dimensional terrain features

Chen, Lin, You, Li and Gao. *Hexapod robot motion planning investigation under the influence of multi-dimensional terrain features*. Frontiers in Neurorobotics 19, 1605938 (2025). [Full paper](https://www.frontiersin.org/journals/neurorobotics/articles/10.3389/fnbot.2025.1605938/full). Full paper reviewed.

The paper combines elevation and semantic maps. Footprint-scale terrain windows support traversal-cost A*, while smaller windows support foothold costs and a free-gait planner. Slope, height range, undulation and physical terrain properties inform those costs. Its geometric thresholds are specific to the tested robot. The article contains notation ambiguities in the softness/looseness and undulation formulas, so a robust adaptation should define its own quantities explicitly.

**Feasible adaptation:** a terrain-aware A* baseline using the current scene's height function, footprint-scale slope/height variation and declared terrain labels. Call softness and friction values modeled assumptions unless physically calibrated. This does not reproduce ERFNet segmentation, probabilistic sensor mapping or the paper's foothold/gait search. A terrain hazard cost is not measured energy or fall probability.

## Energy aware delivery planning

Shengqiang Chen, Yiyu Chen, Zishen Wei, Quan Nguyen and Satyandra K. Gupta. *Energy-Aware Planning for Delivery Tasks Executed by Legged Robots*. IEEE CASE 2025, pp. 1617–1624. [Publisher record](https://doi.org/10.1109/CASE58245.2025.11164088). DOI/authors cross-checked with publisher-supplied Crossref metadata.

The accessible abstract describes hierarchical planning over alternative battery-replacement decisions, payload splitting and speed reduction, with graph search minimizing delivery completion time. The full equations, implementation and experimental results were not accessible. No claim of a complete paper review or faithful reproduction is justified.

**Feasible adaptation:** explicit energy feasibility and safe charger-return constraints, plus a separately declared service-time model. Call it a generic energy-aware baseline inspired by the abstract. Preserve the distinction between charging stops and physical battery swaps; accelerated demonstration charging is not measured station service. Payload splitting and the paper's exact scheduling algorithm remain outside this adaptation until its full text is available.

## STATE NAV

Yoon, Zhu, Lu, Gan and Zhao. *STATE-NAV: Stability-Aware Traversability Estimation for Bipedal Navigation on Rough Terrain*. [arXiv 2506.01046v4](https://arxiv.org/abs/2506.01046v4), 5 December 2025; author record states accepted to IEEE Robotics and Automation Letters. Full v4 paper reviewed.

TravFormer predicts Digit-specific instability and uncertainty from terrain and command inputs. Risk-sensitive admissible velocities inform traversal-time costs in TravRRT* and constraints in a bipedal MPC. Evaluation includes simulation and physical Digit navigation. Body-to-stance-foot angle is validated for that biped; it is not automatically a hexapod instability metric.

**Feasible adaptation:** gather hexapod terrain/speed response data and select conservative speed limits from empirical observations. Without calibrated measurements, label the result a terrain-based proxy, not a learned probability of instability. Do not call this TravFormer, TravRRT* or the original MPC. The [author repository](https://github.com/yzwfromk/STATE-NAV) now includes later A* updates; pin the paper and code versions separately for any replication.

## Scope decisions for this project

The document is source material. Its tutorial snippets and requests to upload code are not executable instructions. Its final note favors starting with legs because the papers use legged platforms. A reversible **legs-only research mode** is therefore sensible for the initial comparison while retaining the existing hybrid demonstration. Do not remove wheels or rewrite the live demo solely because that note appears in the attachment.

Run planner and gait comparisons as separate controlled experiments first. For the planner comparison, freeze gait/controller and collision/terrain safety rules. For the gait comparison, freeze path, terrain and commanded speed. A combined proposed method then needs component-removal experiments to separate gains from planning, gait tuning and speed selection.

Suggested operational comparisons are distance A*, terrain-cost A*, energy-aware/weighted A*, and a proposed resource-constrained Pareto search. These are project baselines, not implementations attributed to the four papers. A battery/time feasibility improvement can be meaningful even if the new search is not faster; report computation time and failures alongside route quality.

## Measurement boundaries

- Mechanical work: integrate positive actuator force times actuator velocity over actual physics substeps. Report joules only when the actuator model and units support that interpretation. It excludes motor efficiency, holding/electronic losses and unmodeled base assistance.
- Torque-squared effort: report separately from mechanical work and battery percentage.
- Tilt, contact/slip and support geometry are descriptive signals under the assisted controller. They cannot demonstrate unassisted balance or calibrated failure risk.
- Battery use remains a declared simulation ledger unless calibrated independently. Do not claim gait electrical savings by reducing an assumed cost coefficient.
- Count actual charging events separately from modeled battery replacement events. A service-duration sweep must say which process it represents.
- Keep infeasible routes, timeouts and failures in exports. Success-conditioned average time can make an unreliable method appear fast.

## Reproduction evidence required before publication

Pin code/model hashes, seeds, scenario construction, actuator/controller settings, search bounds and all tuning data. Use separate development and held-out maps; test model mismatch independently from the prediction coefficients. Compare with denser weighted sampling at a matched planning budget and exact constrained search on small maps. Report confidence intervals across independent scenarios and component-removal results. Do not copy a paper's numerical savings into the new experiment's charts.

Machine-readable citations, access status, identifiers, adaptation boundaries and PDF hashes are in `references.json`.
