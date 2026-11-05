# Making the comparison more reliable

PSO and ACO do not need neural-network training in this project. We tune their search parameters, freeze those settings, then test them on unused cases.

## What the new study runs

1. **Development:** 4 task/obstacle layouts × 2 parameter settings × 2 random seeds × 3 methods = 48 planning attempts. Each method gets the same tuning allowance. Choose the setting admitting the most routes; break ties with the lower common route score. Exact ties retain the default.
2. **Held-out planning:** 12 different task/obstacle layouts × 3 seeds × 3 methods = 108 attempts. Settings are frozen before this stage. There is no retuning to make the proposal win.
3. **Physics check:** 4 cases selected in the original manifest × 3 methods × 1 seed = 12 attempts. Only admitted plans execute; rejected attempts remain visible. This is a small execution check, not 12 independent terrain worlds.

The cases vary starts, goals, deadlines, battery limits, difficulty limits and a real simulated obstacle position. All methods receive the same case, seed and 2-second planning budget. Every case uses the existing terrain, robot and stations. A* initialization and refinement share that budget; common map preparation is reported separately.

## Where to see the results

Open **http://127.0.0.1:8771** and refresh the page. The **Reliability study** section links to the held-out planning and physics records. Select the desired saved run, then click **Use selected run in charts**. Open **http://127.0.0.1:8772/** to see the comparison dashboard.

Start with planning admission, then inspect the paired wins/ties/losses table. Next open the physics run to check measured mission success, time and mechanical work. Planning-only mission success is unavailable. Equal numbers are legitimate if the methods select the same route; do not add artificial randomness to separate them.

Download CSV for the attempt table and JSON for routes, parameters, source hashes and measurements. The complete study files are in `mujoco/outputs/research/reliability_v1/`:

- `manifest.json`: cases and parameter candidates fixed before tuning.
- `locked_parameters.json`: selected parameters, written before held-out testing.
- `development_default.json` and `development_alternative.json`: tuning evidence.
- `heldout_planning.json` and `heldout_physics.json`: separate evaluations.
- `comparison.json`: paired outcomes and descriptive uncertainty.
- `study_summary.json`: links and summary across stages.

## What the numbers mean

The common score combines modeled distance, time, battery use and terrain exposure. Lower is better only when the limits are met. A lower modeled score does not guarantee lower measured work. Mechanical work is not electrical battery energy.

Paired score comparisons use cases where both methods are admitted; the other outcomes are counted separately. Descriptive bootstrap intervals average repeated seeds inside each layout, then resample whole layouts. This avoids counting three seeds as three independent maps. Intervals remain conditional on the fixed scene and jointly admitted cases; small samples cannot establish broad superiority.

## Run it again

From the `mujoco` folder:

```bash
python3 -m research.reliability
```

This resumes completed phases in the same study directory; it does not create extra evidence by rerunning saved phases. Keep its manifest unchanged. To conduct a new, genuinely independent study, define new seeds/cases in a new study version before running it. Merely using a new directory with the current command generates the same cases. Preserve the old results and code snapshots.

## Recommended next experiment

Before changing the algorithm, examine which limits cause rejections and whether performance differences matter. Improve the proposed method using development cases only. Compare with simple A* and greedy ablations as well as PSO/ACO. Use fresh evaluation cases after further tuning; the current held-out results become development evidence once you use them to guide changes.

For stronger research evidence, next add independently generated terrain maps and validate the terrain/collision model, then test disturbance scenarios and battery/energy calibration. After measuring runtime, predeclare a larger feasible campaign (for example 30 independent terrain maps and 5 paired seeds per method). That number is a practical starting plan, not a guarantee of sufficient statistical power or publication. Include confidence intervals, every failed attempt, ablations and limitations.

The robot currently uses assisted chassis motion, posture and gravity compensation. Results do not establish unassisted real-robot stability. Publication potential depends on a defensible new contribution, fair comparisons and validation; no acceptance percentage can be estimated from this pilot.

Methodology reference: [COCO experimental procedure](https://numbbo.github.io/coco-doc/experimental-setup/) discusses optimization budgets, instances and repeated runs. This project uses its own robotics benchmark; it is not a COCO benchmark implementation.

## Observed planning results from this study

Run `20261028T013210063968Z`: all three methods admitted 9/36 attempts (25%). Of the nine paired admitted comparisons, proposed versus PSO had 4 lower scores and 5 ties; proposed versus ACO had 3 lower scores and 6 ties. Differences were small, and the descriptive layout intervals include zero. Only three layouts contributed admitted paired scores, so this does not establish overall superiority.

For the proposed method, 21 attempts exceeded battery plus return reserve, six returned no route, and six exceeded the deadline. Limit violations overlap; these counts must not be added as disjoint categories. Nine attempts met the limits. Investigate mission energy and return planning on development cases before claiming that a larger search population will solve the main problem.

Physics run `20261028T013448551391Z`: 12 attempts, nine resource rejections and three completed executions. All methods used the same selected route on the executed case, so their measured time (72.848 seconds) and mechanical work (16,385.631 joules including return) were identical. This is a legitimate deterministic tie and provides no physical-performance advantage for the proposal.

Validation: 12 unit checks passed, including physical/navigation obstacle consistency, parameter isolation and paired denominators. The independent study audit passed for all 168 attempts, including archived source hashes, frozen choices, unique trial keys and CSV reconciliation. Dashboard compilation and local HTTP endpoints passed. Interactive browser visual checks were unavailable because the browser-control tool exposed no browsers.

Next development priority: calibrate modeled battery drain and examine station-stop/return planning. If adding station choices, give every compared method the same available actions and constraints. Keep future evaluation cases separate from these now-inspected results.
