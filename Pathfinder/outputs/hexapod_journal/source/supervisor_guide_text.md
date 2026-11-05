Hexapod study explanation and publication readiness

Prepared for discussion with your supervisor 28 October 2026


# 1 Is the study ready for a journal

There is enough material for a detailed preliminary manuscript and a useful supervisor meeting. The present evidence is not yet strong enough to support a broad claim that the proposed system outperforms existing methods in a Q2 or Q3 research submission. A polished paper cannot replace missing experiments. Acceptance cannot be predicted as a reliable percentage.

The main result is honest but limited. All three methods accepted 25% of the held-out planning attempts. The proposed method obtained a slightly smaller modeled route score in some accepted comparisons. Only one case actually executed per method in the physics check, and those measurements were identical. The manuscript reports these results without inventing an advantage.

What is already available

What is already available
Item | Current evidence
Working research software | Experiment console, comparison website, route logs and downloads
Recorded primary study | 48 tuning attempts + 108 planning tests + 12 physics attempts
Separate tuning and test cases | 4 development layouts and 12 unused evaluation layouts
Measured physics | 3 completed executions on the same case; 9 rejected plans
Manuscript and figures | A full journal-style draft, six original figures and numbered references



The Word manuscript follows a conventional research-paper structure. It uses the Journal of Intelligent & Robotic Systems instructions as a formatting reference: a 150–250-word abstract, four to six keywords, decimal headings, numbered citations and declarations. This is a style choice, not a claim that the journal has endorsed the work or that its current quartile has been verified. [G1]


# 2 Understand the system in simple words

The hexapod is a six-legged robot. The simulator is its virtual test environment. A planner chooses where its body should travel. The controller makes the simulated robot follow that route. The evaluator checks time, battery and terrain limits.

PSO is a group of candidate routes that learn from good previous candidates. ACO builds routes using reinforced connections. The proposed method keeps useful partial routes and removes ones that are worse in every recorded cost. All three begin with safe A* routes, so they can select the same final path.

Multiobjective means considering several goals together. Here the goals are short distance, short predicted time, low modeled battery use and low terrain exposure. The software combines them into one declared score after checking limits. It does not prove that one route is best for every possible preference.

System overview  The Research Lab runs the experiment; the comparison website shows the saved results. AI-assisted plotting code used the archived data or documented implementation.

[Figure: figure_1_system]


# 3 Use the two websites

Open the Research Lab to choose settings, launch an experiment and inspect saved records. Open the Method Comparison website to compare the saved methods. You do not need to run the robot again just to view an existing result.

Research Lab  

Method Comparison  

These are local addresses. They work on the computer running the project and are not public links for your supervisor. Share the Word documents and evidence files, or arrange an authorized deployment later. Open the website address rather than double-clicking a split-build HTML file.

To view the main study, find Reliability study in the Research Lab and choose held-out planning or held-out physics. Select that saved run, click Use selected run in charts, then open Method Comparison. Use the scenario and repetition filters for a matched comparison. The paired-outcome table is explicitly labeled as the full held-out set and does not change with those filters.

A short demonstration experiment

A short demonstration experiment
Setting | Choose | Reason
Suite | Pilot with 3 scenarios | More informative than the one-task smoke check
Methods | PSO versus ACO versus Proposed | Directly compare the three main methods
Repetitions | 3 | Inspect sensitivity to paired random seeds
Planner budget | 2.0 seconds | Same nominal search allowance for every method
Locomotion | Walking only | Keep the movement mode fixed
Execution | Plan and run MuJoCo physics | Obtain measurements if the route passes its limits
Service | Modeled charging stop | Keep the terminal service rule consistent



This demonstration schedules 27 attempts: 3 scenarios × 3 methods × 3 repetitions. It is not part of the manuscript’s frozen primary study unless a later version explicitly analyzes it. A two-second planner budget is time for route search, not robot travel time and not a charging interval. The current mission checks battery for the destination and return; it does not recharge every two seconds.


# 4 Read the results correctly

Meaning of common outcomes and missing values

Meaning of common outcomes and missing values
Display | Simple meaning
found or admitted | A returned route passed the predicted limits
resource_rejected | A route was found, but battery, deadline or exposure failed
no_route | No route was returned under this search configuration; not proof of impossibility
Unavailable predicted value | The algorithm returned no route from which to calculate it
Unavailable measured value | Physics did not execute, or this was a planning-only run
Equal measured numbers | The same path and deterministic controller can give the same result



For planning, use admission rate, route score and planning time. For executed missions, use measured destination time, mechanical work and mission completion. Keep their denominators visible. The common score is an estimate. Mechanical work is not electrical battery energy. Small assisted tilt does not prove real-robot balance.

The main study has 36 planning attempts per method. Each method admits nine, rejects 21 for resources and returns no route in six. The 21 resource rejections all exceed battery plus return reserve; six also exceed the deadline. The overlap explains why failure-reason counts do not add up as separate categories.

Among nine paired admitted trials, proposed versus PSO has four lower scores and five ties. Proposed versus ACO has three lower scores and six ties. These nine trials come from only three layouts. The small score advantages do not establish a general winner. On the executed physics case, all three take 72.848 seconds to reach the destination and perform 16385.631 J of positive actuator work for the mission including return.


# 5 What is still missing

Priority gaps before a strong submission

Priority gaps before a strong submission
Priority | Gap | Required evidence
1 | A clearly new research contribution | Explain what is new beyond combining known A*, PSO, ACO and label-search ideas
2 | Broader independent environments | Use new terrain families, not only one scene with a moved obstacle
3 | More informative feasible cases | Balance feasible and challenging tasks without selecting proposed-method wins
4 | Stronger matched baselines | Include simple A*, greedy shortcuts and an exact small-graph constrained reference
5 | Component-removal comparisons | Measure the value of portfolio seeds, resource pruning, heading labels and caps
6 | Physical and energy validity | Calibrate battery assumptions and external assistance; add hardware or stronger dynamics validation for physical claims
7 | Adequate uncertainty and robustness | Predeclare effects, seeds and disturbances; report layout-level intervals and all failures
8 | Complete submission package | Resolve authorship, funding, conflicts, licenses, data archive and AI disclosure



Real-robot hardware is not a universal requirement for every simulation paper. It becomes essential, or needs a persuasive alternative, when the manuscript claims hardware energy savings, autonomous balance or practical physical deployment. A simulation-only paper must make a defensible contribution within its stated scope.


# 6 Recommended next experiment

Step 1  Discuss the research claim with your supervisor. Choose one measurable contribution. One candidate is better use of planning time when common A* initialization fails. Another is a calibrated mission-level return or station-stop policy. These are research directions, not demonstrated improvements.

Step 2  Work on development cases only. Investigate the six timeout records and test whether unused refinement time can return to the seed search. Give the same initialization policy to PSO and ACO for a fair refiner comparison. Check whether the battery coefficients describe the intended robot before changing limits.

Step 3  Add matched baselines and component-removal tests. A simple method is a valuable baseline: the proposed system must justify its added complexity. When station actions or terrain information change, all compared methods should receive the same available actions and information.

Step 4  Create a new evaluation set before further tuning. As a planning example, 30 independent terrain maps × 5 paired seeds × 5 methods produces 750 attempts at one fixed planning budget. First estimate runtime with a small development pilot. Thirty maps is an example, not a guarantee of enough statistical power. Select the final sample using the practical effect of interest and variability. Keep a range of terrain difficulty, route lengths and feasible resource profiles.

Step 5  Freeze the final method. Test once on the new evaluation set. Keep rejected plans, timeouts and ties. Report both all-attempt coverage and conditional route costs. Use layout-level paired uncertainty and an appropriate predeclared test if the independent sample supports it. After inspecting a test set to improve the algorithm, treat that set as development evidence.

Step 6  Validate execution on several preselected scenarios per terrain family. Measure disturbances, collision behavior and model mismatch. Calibrate electrical battery claims with an appropriate measurement model or hardware. Evaluate assistance reductions only with clear controls and failure reporting.


# 7 Suitable journals and how to choose

Q2 and Q3 are journal-ranking categories, not universal manuscript templates or acceptance percentages. Rankings depend on database, subject category and year. Current authoritative JCR or SCImago category records were not verified in this preparation, so the shortlist below is based on publisher scope rather than a certified Q2/Q3 label. Confirm the required database and year with your supervisor or university library before choosing a target.

Scope-based shortlist for supervisor discussion

Scope-based shortlist for supervisor discussion
Journal | Why consider it | Current obstacle
Journal of Intelligent & Robotic Systems | Robot planning and intelligent robotic systems fit the topic | Needs stronger novelty and evaluation; use its official author instructions [G1]
Robotica | Broad robotics, task planning and realistic applications [G2] | Needs a convincing robotics contribution beyond a small assisted benchmark
Industrial Robot | Possible later application-focused option [G3] | Consider only after establishing a realistic industrial task and practical validation



For each candidate, check recent papers with similar methods, actual scope, article type, current quartile in the required category, open-access conditions, fees or institutional agreements, word limits and figure requirements. A ranking does not determine whether your manuscript fits the editor’s priorities. Do not pay an intermediary promising acceptance.

The manuscript uses a conventional introduction, related work, method, experiment, results, discussion, conclusion, declarations and references. Journal-specific format must be checked again after a target is selected. Word acceptance, abstract length and citation style were checked in the Journal of Intelligent & Robotic Systems guidance. [G1]


# 8 Submission steps

First agree on authorship and the contribution with your supervisor. Complete the missing experiments and update every affected result, chart and claim. Then select one journal and follow its current author instructions. Do not submit the same manuscript to multiple journals at the same time.

Prepare the final manuscript, separate figure files, evidence archive, data-availability statement and cover letter. Confirm that all authors approve the submission and that funding, conflicts and model-asset licenses are accurate. The present placeholders must be completed with real details, not assumed values.

Disclose AI assistance and retain human responsibility. [G4] This work involved AI assistance in implementation, analysis, drafting and figure code, not only grammar editing. The human authors must understand and verify the methods and conclusions. Cambridge’s instructions also address disclosure of AI-assisted visual content. [G2]

Upload through the selected journal’s official portal. Answer editorial questions accurately. If reviewers request changes, respond point by point and identify exactly what changed. No submission, email to editors or public publication has been performed as part of preparing these files.


# 9 A short explanation for your supervisor

“I built a simulation lab to compare three route-planning methods for a hexapod: PSO, ACO and a proposed bounded Pareto refiner. They share the same tasks, collision checks and declared planning budget. I separated parameter-tuning cases from test cases and saved every failure and tie. The proposal sometimes has a slightly better predicted score, but all methods have the same admission rate. Physics evidence is still limited, so I need stronger baselines, independent terrains and better validation before claiming a publishable performance improvement.”

If asked why the results are equal, say: “They often choose the same route from the shared initialization, so equal outcomes are expected.” If asked why there are missing values, say: “Some routes were not returned or were rejected, so no physics measurement exists.” If asked whether the method is ready for hardware, say: “The current simulator assists body movement, so that has not been demonstrated.”


# Sources for journal preparation

[G1] Journal of Intelligent & Robotic Systems submission guidelines. Checked 28 October 2026.

[G2] Robotica author instructions and preparing your materials. Checked 28 October 2026.

[G3] Industrial Robot publisher journal page. Publisher scope was available in its search record; detailed page access was blocked and current requirements must be checked.

[G4] Springer Nature policy on AI use in manuscript preparation. Checked 28 October 2026.

The scientific references and source-access boundaries appear in the manuscript. The data analysis uses the frozen primary study, not an invented or regenerated dataset. Authorship, the final journal selection and human approval remain for the research team.