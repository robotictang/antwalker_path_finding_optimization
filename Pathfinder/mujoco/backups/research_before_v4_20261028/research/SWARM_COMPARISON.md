# PSO ACO and the upgraded proposed planner

The lab now offers **PSO vs ACO vs Proposed** as a three-method group. The
original A* baselines remain available. **Greedy vs Previous vs Proposed** is an
ablation group that checks whether more sophisticated refinement adds value.

PSO and ACO are established algorithms; they are new additions to this project.
Adding them alone does not establish a novel research contribution.

## Implemented methods

**B5 PSO with a safe A* seed.** Sixteen particles hold continuous random keys
for intermediate waypoint inclusion. They update velocities using inertia,
their personal best and the swarm best, then update bounded positions. Unsafe
omissions are repaired along the original safe corridor. Both the unmodified
seed and a simple greedy shortcut are included in initialization.

**B6 ACO with a safe A* seed.** Twelve ants per iteration construct waypoint
subsequences using collision-checked forward connections. Choices depend on
pheromone strength and geometric progress. Pheromones evaporate; constructed
routes and the best retained route deposit additional pheromone. This is an
elitist Ant-System-style adaptation, not an exact reproduction of ACS.

**Proposed portfolio Pareto refinement.** Retains the common safe incumbent
and uses heading-aware, resource-constrained labels on visible waypoint
connections. Battery/time lower bounds prune impossible prefixes, while
non-dominated labels preserve different trade offs. Walking costs remove the
single start/stop allowance before accumulating edges. The hybrid-mode fallback
uses whole-route beam evaluation because mode transitions complicate additive
costs. A timeout retains a feasible incumbent. Label and expansion caps make
this approximate; it has no global optimality or universal superiority guarantee.

**B7 Energy plus greedy shortcut.** Stops after common seed initialization.
This deliberately simple comparison helps reveal whether any gain comes from
swarm search or merely from removing unnecessary waypoints.

**Previous proposed planner.** Preserves the preceding seeded grid Pareto
implementation under `proposed_v1` for a direct upgrade comparison.

## Equal comparison conditions

All methods use the same robot, known obstacles, terrain speed limits, departure
heading, battery-and-charger reserve check and continuous clearance criterion.
Seeds, visibility queries, optimization and metric evaluation are charged to the
total per-method wall budget. Common graph/lower-bound preprocessing is reported
separately. Graph expansions and fitness evaluations are different operations
and must not be compared as if they were the same unit.

New methods rank feasible routes ahead of infeasible ones, then use this common
preference: distance/50 + predicted time/90 + modeled energy/30 +
0.25 × terrain exposure/20. Feasibility is based on the same deadline, battery
and terrain budgets. Failed and rejected attempts remain in denominators.

PSO and ACO are **hybrid seed-and-refine baselines**, not standalone unseeded
global algorithms. Version `common_seed_portfolio_v2` gives PSO, ACO, greedy
and the proposal the SAME energy/time/distance seed-generation recipe and
30 percent seed-time allocation. Each optimizer shares one remaining wall
budget and a total cap of 240 whole-route fitness evaluations across corridors.
PSO/ACO iteration limits apply per corridor. The proposal also records its
separate edge-metric and label-expansion work; these are not equivalent to
whole-route evaluations. All work is charged to wall time. Parameters are
recorded, but have not been extensively tuned on held-out maps.

Earlier energy-seed-only development runs remain in history. Their source
snapshots and saved names must not be confused with the common-portfolio study.

Each repetition gives the same case seed to all methods. A random seed
controls optimizer sampling and method order; the three scene cases are still
not independent generated maps. Keep repeats separate from map diversity.

## Run from the website

1. Open http://127.0.0.1:8771 and refresh the page.
2. Select **Smoke**, **PSO vs ACO vs Proposed**, **1 repetition**, **2 seconds**,
   **Walking only**, **Plan and run MuJoCo physics**, and **Modeled charging stop**.
3. Run once and wait for completion, then open the comparison page.
4. Next select **Pilot**, keeping the other settings unchanged.
5. For optimizer variation, use **3 repetitions**. Start with planning only if
   you want a faster check; it does not measure actual simulated execution.

The dashboard filters scenarios and repetitions, includes PSO and ACO in route
comparisons, and plots recorded best-feasible search progress. Early termination
or equal routes are legitimate results. More computation is not automatically
better performance.

## Command line

From `mujoco/`:

```bash
python3 -m research.run --suite pilot --methods pso aco proposed --repeats 3 --planning-seconds 2
python3 -m research.run --suite pilot --methods pso aco proposed --repeats 1 --planning-seconds 2 --execute
python3 -m research.run --suite pilot --methods b7_greedy proposed_v1 proposed --repeats 3
```

## Before claiming that the proposal is better

Compare feasibility and successful execution before successful-only cost means.
Report paired route-score differences, execution time, modeled battery use,
mechanical work, planning time and uncertainty. Include independently generated
held-out maps, tuned stronger baselines, several optimizer seeds and ablations.
Avoid tuning on the same cases used for the final claim. Benefits on these
three assisted-model cases do not establish hardware performance or publication
novelty. Real electrical energy and fall probability remain unvalidated.

Algorithm sources: Kennedy and Eberhart 1995, *Particle Swarm Optimization*
(https://staff.washington.edu/paymana/swarm/kennedy95-ijcnn.pdf), and Dorigo and
Gambardella 1997, *Ant Colony System*
(https://staff.washington.edu/paymana/swarm/dorigo97-itec.pdf). Adaptations and
access notes are recorded in `references.json`.
