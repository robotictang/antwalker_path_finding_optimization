"""Extend the complete V4 manuscript; never overwrite the original draft."""
from pathlib import Path
import json,re
B=Path(__file__).resolve().parents[1];OLD=B.parent/'ieee_access_v4';A=json.loads((B/'source/extension_analysis.json').read_text())
S=B.parents[1]/'mujoco/outputs/research/validation_extension_v5';audit=json.loads((S/'audit.json').read_text());selection=json.loads((S/'locked_parameters.json').read_text())
P={r['method']:r for r in A['primary']};R={r['baseline']:r for r in A['comparisons']}
def effect(method):
 r=R[method];lo,hi=r['relative_ci95'];return f"{r['mean_relative_percent']:.3f}% (descriptive 95% interval [{lo:.3f}, {hi:.3f}]%)"
def ptext(x):return '<0.0001' if x<.0001 else f'{x:.4f}'
text=(OLD/'source/manuscript.md').read_text()
abstract=f'''Hexapod route planning must balance distance, destination time, battery capacity, and terrain difficulty under a finite computational allowance. This article presents a resource constrained planner combining a safe corridor solution, visibility search, and continuous waypoint refinement. A shared evaluator ranks feasibility before a fixed balanced score. An initial frozen campaign contains 1,232 attempts, with eight development worlds and 24 separate primary test worlds. The proposed V4 configuration admits 69 of 72 primary attempts versus 66 for each alternative. Its world averaged balanced-score gains are approximately 2.07% over seeded particle swarm and ant colony optimization, falling below 1% against controls with identical waypoint polishing. A prospective extension adds 800 attempts and 48 untouched test worlds. Each of four competitive configurations receives the same two-profile development opportunity before settings are frozen. On fresh primary tests, V4 and an adaptive V5 candidate each admit 94 of 96 attempts, versus 92 for each polished swarm control. Their paired score advantages over these controls are approximately 1.42% and 1.41%. V5 returns identical saved route coordinates to V4 in all 96 matched attempts and does not improve mean planning time. Feature removal, shorter budgets, candidate ceilings, and reduced-assistance execution retain unfavorable outcomes. The evidence supports conditional simulation gains and the importance of strong representation controls, while rejecting a superiority claim for the adaptive extension. Electrical battery savings, unassisted locomotion, and hardware transfer remain unverified.'''
assert 150<=len(abstract.split())<=250,len(abstract.split())
text=re.sub(r'(?s)(@ABSTRACT\n).*?(\n\n@KEYWORDS)',lambda m:m[1]+abstract+m[2],text,1)
text=text.replace('## VII Discussion and Limitations','## VIII Discussion and Limitations').replace('## VIII Conclusion','## IX Conclusion')
intro='A prospective extension additionally evaluates an adaptive search candidate, V5, against V4 and independently tuned polished swarm controls on 48 untouched worlds. Its 800 scheduled attempts cover primary planning, feature removal, budget and candidate-cap sensitivity, and two controller-assistance settings. This extension tests whether an apparently more elaborate planner adds value; unsuccessful enhancements are retained rather than promoted as improvements [@evidence].'
text=text.replace('## II Related Work',intro+'\n\n## II Related Work',1)
abtexts=[]
for r in A['ablations']:
 name={'proposed_v5_fixed':'fixed-allocation control','proposed_v5_no_polish':'no-polishing control','proposed_v5_no_landmarks':'no-landmark control'}[r['baseline']]
 abtexts.append(f"Against the {name}, V5 records {r['wins']} wins, {r['ties']} ties, and {r['losses']} losses on jointly admitted pairs; its world averaged score difference is {r['mean_relative_percent']:.3f}%.")
cap=[r for r in A['sensitivity'] if r['cap']==80]
captext=' '.join(f"Against { {'proposed_v4':'V4','pso_polished':'polished PSO','aco_polished':'polished ACO'}[r['baseline']]}, the 80-candidate phase gives {r['mean_relative_percent']:.3f}% mean paired score improvement ({r['wins']} wins, {r['ties']} ties, {r['losses']} losses)." for r in cap)
phys=' '.join(f"At assistance {scale:g}, {sum(r['executed'] for r in A['physics'] if r['assistance']==scale)} of 48 scheduled attempts execute, with {sum(r['successful'] for r in A['physics'] if r['assistance']==scale)} successful missions." for scale in [1.,.5])
early=P['proposed_v5']['bound_exits'];slow=100*(P['proposed_v5']['mean_planning_s']/P['proposed_v4']['mean_planning_s']-1)
section=f'''## VII Prospective Validation and an Adaptive Candidate
### A Frozen Extension Protocol
The extension is a separate prospective campaign, not a replacement for the original test records. Eight fresh development worlds use seeds 1,470,000-1,470,007; 48 fresh test worlds use 1,480,000-1,480,047. Each test family contains 12 worlds. Development, new test, and original V4 world hashes are disjoint. Map-generation and task-limit distributions are retained, so this is within-distribution replication rather than an out-of-distribution claim [@evidence]. Implementation, analysis and drafting assistance are disclosed in [@codex].

V4, polished PSO, polished ACO, and V5 each receive two complete parameter profiles on the same eight development worlds, with one repetition per profile. This gives 64 development attempts. Admission is maximized before admitted mean Q is minimized; exact ties retain the default. All four methods select the default profile. In contrast to the original study's inherited polished controls, each stronger control now selects its own complete swarm and polishing profile. The choices and scientific source hashes are saved before fresh evaluation. No setting is changed in response to fresh test outcomes.

[[TABLE:extprotocol]]

The primary phase has 48 worlds, two paired repetitions, four configurations and 384 attempts. The first 16 predeclared worlds supply feature tests and the 80-candidate sensitivity; the first eight supply 0.5 and 1 s tests; the first 12 supply two assistance conditions. Secondary phases reuse subsets and do not increase the independent test-world count. The campaign completes all 800 scheduled attempts. It is parameter selection and simulation evaluation, not neural-network training.

### B Adaptive Candidate and Feature Controls
V5 tests three changes to V4's bounded search. It evaluates a direct connection before initialization and can stop when a feasible direct route is within a small relative gap of an optimistic score. The bound uses straight-line distance, maximum walking speed, the single start/stop allowance, zero turning, and zero terrain exposure under the same nominal cost model. The default relative tolerance is 0.002. This is a model-specific stopping rule; it is not a theorem about the physical robot or unrestricted terrain models.

The default initial-stage fraction is 0.25 when a direct route is clear and 0.40 otherwise. The corresponding roadmap-stage fractions are 0.20 and 0.45, measured against the total allowance, and the candidate roadmap permits up to 52 valid nodes. A fourth internal search emphasizes terrain exposure. When the incumbent violates a resource constraint, the internal search targeting its largest normalized pressure runs first. Deadline pressure is predicted time divided by deadline; battery pressure is required battery including return reserve divided by available charge; terrain pressure is exposure divided by its limit. Final candidate ranking always uses the unchanged feasibility-first balanced objective.

[[ALG:v5]]

The fixed-allocation control disables direct-bound stopping and resource-prioritized search, restoring the selected V4 stage fractions while retaining the V5 node cap and direct-first ordering. It therefore tests this adaptation bundle, not every isolated decision separately. The other variants remove polishing or landmarks. All inherit the selected V5 settings, preserve endpoints and collision checking, and retain the best registered route at termination. These controls do not receive an extra test-informed tuning opportunity.

### C Fresh Primary Results and Uncertainty
V4 and V5 each admit 94/96 primary attempts; both polished controls admit 92/96. The additional admissions correspond to one world over two repetitions. Another world is rejected by all four configurations. Admitted-only means involve different populations, so the paired effects below remain the comparison basis.

[[TABLE:extmain]]

V5 and V4 return exactly the same saved waypoint coordinates in all 96 matched attempts, including the rejected pair. Their 94 jointly admitted score comparisons are therefore ties, with no evidence of a route-quality advantage for V5. Both methods have identical paired score effects against the polished controls. Relative to polished PSO the world averaged improvement is {effect('pso_polished')}; relative to polished ACO it is {effect('aco_polished')}. Joint admission supplies 46 worlds and 92 paired repetitions for each swarm contrast. The median world-level improvement is zero against both controls. The largest improvement is 41.114% in one world; excluding that largest effect as a post hoc diagnostic reduces the means to approximately 0.536% and 0.531%. The official complete-set effects retain that world. Thus the average gain does not describe a typical improvement on every map.

[[TABLE:extpaired]]

Intervals again use 5,000 whole-world bootstrap resamples after averaging paired repetitions. The analysis plan was saved after primary execution began but before inspection of held-out scores; it was not externally preregistered. It adds exploratory two-sided sign-flip tests of world-mean score differences, using 100,000 Monte Carlo sign assignments, seed 7421, a plus-one correction, and Holm adjustment over the three primary V5 contrasts. Adjusted p-values are {ptext(R['proposed_v4']['holm_p'])} against V4, {ptext(R['pso_polished']['holm_p'])} against polished PSO, and {ptext(R['aco_polished']['holm_p'])} against polished ACO. These tests assume sign exchangeability under the null and condition on joint admission. They are exploratory, not a guarantee of practical benefit, and they do not replace effect sizes or execution evidence.

[[FIG:ext1]]

### D Feature Removal and Budget Sensitivity
{' '.join(abtexts)} These counts cover the first 16 worlds with two repetitions, and the remaining admission categories stay in the archived records. An apparent component benefit is specific to this bounded implementation and subset; the fixed-allocation control removes several adaptation decisions together.

[[FIG:ext2]]

The shorter-budget comparison uses the same first eight worlds at 0.5 and 1 s with one repetition, alongside their two-repetition 2 s results. Figure 10 therefore compares a consistent map subset while disclosing the repetition difference. The candidate-ceiling phase separately uses 16 worlds, a 2 s allowance and at most 80 whole-route evaluations. {captext} Neither sensitivity establishes dominance for every available budget.

[[FIG:ext5]]

### E Computation and Identical-Route Diagnosis
Mean planner time is {P['proposed_v4']['mean_planning_s']:.4f} s for V4 and {P['proposed_v5']['mean_planning_s']:.4f} s for V5, a {slow:.2f}% increase for V5 on this machine. Its direct-bound rule triggers {early} times in 96 primary attempts. The proposed enhancement therefore does not demonstrate an efficiency or quality gain over V4 on this fresh set. V4 remains the supported main configuration; V5 is retained as a negative enhancement result.

[[WIDEFIG:ext3]]

The new instrumentation counts all calls to the common continuous metric evaluator within each method's planner invocation, including roadmap edge calculations and final route reevaluation. It excludes shared preparation. Counts are distinct from whole-route fitness evaluations, visibility checks and search expansions; one metric call can itself integrate segments of different lengths. Thus the 80-candidate phase equalizes a ceiling, not actual evaluations or total computational work. Per-trial wall time and operation counts are supplied together.

Identical output geometry is checked directly from saved arrays, not inferred from rounded chart labels. Separate trial keys, timers and source records are retained for V4 and V5. Shared initial corridors and the same local polishing operator can converge to the same route, and the extra V5 exploration fails to change the incumbent here. These observations warrant a tie, not fabricated metric differences or an assertion that V5 is better.

### F Assistance Sensitivity and Physical Scope
{phys} Every method has 12 scheduled tasks per condition. The success denominator includes rejected plans; executed-only rates are a separate quantity. Table 13 reports each method and condition with conditional time/work means. Unexecuted attempts have unavailable physical metrics, not zero time or energy.

[[TABLE:extphysics]]

[[FIG:ext4]]

Assistance 1 reproduces the original commanded body-velocity and posture overwrite. Assistance 0.5 blends the current and commanded body velocities with equal weights at each relevant update; posture blending occurs at the control interval and horizontal/yaw blending at each physics substep. This is not a 50% reduction in force or external energy, and its repeated application can still impose substantial motion guidance. In both conditions, all four methods time out on v5test_02 before reaching the destination. The standard setting records approximately 0.904 m motion and 10,900 safety stops over 180 s, with zero recorded obstacle penetrations or solver warnings. The reduced setting records approximately 0.913 m and 10,898 safety stops. These records identify persistent safety stopping with minimal progress; they do not independently establish its physical cause. Static route admission therefore does not guarantee executable closed-loop progress. The controller and gravity compensation remain enabled. Even successful reduced-assistance trials do not validate unassisted locomotion. Mechanical actuator work still excludes the cost of body guidance; no electrical coefficient is fitted to these values.

### G Extension Integrity and Interpretation
The extension audit passes {audit['attempts']} unique scheduled records across nine phases, reconstructs {audit['unique_routes_collision_checked']} distinct saved routes, and recomputes {audit['recomputed_metrics']} continuous metric values. It checks archived sources, models, world hashes, settings, paired seeds, candidate ceilings, score arithmetic, admission and execution success. Independent manuscript calculations reconcile all primary paired counts and percentages with the archived report. Thirty-seven distinct automated checks passed before the scientific source freeze; a final suite of 40 distinct checks also passes after the service-delivery changes. The original 1,232-attempt campaign remains unchanged.

This extension strengthens within-distribution evidence and baseline tuning fairness. It also rejects the expectation that a more elaborate search policy necessarily improves results. It does not address moving obstacles, uncertain perception, unrestricted continuous swarm representations, additional planner families, real electrical calibration, or hardware operation. Illustrative fresh-route panels and all world-level subgroup effects are supplied in Supplementary Evidence S2; complete-set results, rather than selected panels, control the conclusions.

'''
text=text.replace('## VIII Discussion and Limitations',section+'## VIII Discussion and Limitations',1)
text=text.replace('Twenty-four test worlds and five executed physics worlds per method provide limited coverage.','The original campaign has 24 test worlds and five executed physics worlds per method. The extension adds 48 disjoint test worlds and two assistance conditions on a 12-world subset, but all remain within the same restricted generator.')
text=text.replace('The reported bootstrap intervals are descriptive, conditioned on paired admission for scores, and uncorrected for multiple comparisons.','The original bootstrap intervals are descriptive, conditioned on paired admission for scores, and uncorrected for multiple comparisons. The extension adds exploratory Holm-adjusted tests for three primary contrasts; conditioning and modeling limitations remain.')
text=text.replace('The next scientific priority is an independently planned evaluation of when landmark diversification helps enough to justify its cost. This should use new worlds and settings chosen without consulting the present held-out outcomes.','The prospective extension supplies an additional independently planned evaluation and does not establish an advantage for the adaptive allocation candidate over V4. The next scientific priority is to identify a more effective diversification mechanism using new development maps, then freeze it before further test maps are generated.')
text=text.replace('For physical relevance, the controller should be tested with reduced body assistance and its full energy cost included.','The reduced-assistance blending test is a sensitivity check, not an unassisted controller demonstration. For physical relevance, a dynamically actuated controller must be evaluated with direct body-velocity overwrites removed and all assistance energy explicitly accounted for.')
text=text.replace('These are future validation steps, not experiments claimed to have been completed.','Electrical calibration, genuinely unassisted locomotion, and hardware operation remain future validation steps.')
text=text.replace('Broader baseline coverage, independent worlds, reduced controller assistance, and electrical calibration are needed before extending the claims to robust hardware operation.','The separate 800-attempt extension replicates conditional gains against individually tuned polished controls on 48 fresh worlds. However, its adaptive V5 candidate returns the same 96 routes as V4 with a higher mean planner time. The enhancement is therefore not promoted over V4. Broader baseline coverage, out-of-distribution worlds, unassisted control, and electrical calibration remain necessary before extending the claims to robust hardware operation.')
text=text.replace('The frozen V4 records, source snapshots, model XML files, settings, audit output, and reproduction instructions are supplied with this draft as Supplementary Evidence S1, identified in [@evidence].','The frozen V4 records are supplied as Supplementary Evidence S1. The prospective 800-attempt extension, its settings, source snapshots, model XML, audits, independent analysis, world-level effects, and reproduction instructions are supplied as Supplementary Evidence S2, identified in [@evidence].')
text=text.replace('No new training results have been added to the frozen campaign for manuscript preparation.','The original campaign has not been altered. S2 is a separately frozen parameter-selection and evaluation campaign, not a neural-network training result. Its relocation copy distinguishes path-only XML edits from the unchanged archived model and source hashes.')
text=text.replace('Assisted physics produced equal completion counts across methods.','The original assisted physics phase produced equal completion counts across methods.')
text=text.replace('but the primary generalization sample remains 24 generated worlds','but the original primary generalization sample remains 24 generated worlds')
text=text.replace('[[FIG:ext4]]\n\n','')
text=text.replace('### G Extension Integrity and Interpretation','[[FIG:ext4]]\n\n### G Extension Integrity and Interpretation',1)
text=text.replace('Sections I–VIII','Sections I–IX')
(B/'source/manuscript.md').write_text(text)
refs=json.loads((OLD/'source/references.json').read_text());refs['evidence']['text']='Tomato, "Frozen V4 hexapod campaign and prospective V5 validation extension," unpublished research software and simulation records, Oct. 2026, Supplementary Evidence S1 and S2. Original campaign: 1,232 attempts, 24 primary test worlds; separate extension: 800 attempts, 48 disjoint primary test worlds. No public repository identifier assigned.'
(B/'source/references.json').write_text(json.dumps(refs,indent=2))
builder=(OLD/'source/build_manuscript.py').read_text().replace("final=B/'IEEE_Access_Hexapod_V4_Manuscript.docx'","final=B/'IEEE_Access_Hexapod_Validated_Manuscript.docx'")
builder=builder.replace('IEEE Access template research manuscript draft reporting the frozen V4 simulation campaign','IEEE Access manuscript reporting V4 and a separately frozen prospective validation extension')
extra='''
EXT=json.loads((B/'source/extension_analysis.json').read_text())
EN={'proposed_v4':'V4 retuned','pso_polished':'PSO + polish','aco_polished':'ACO + polish','proposed_v5':'V5 candidate'}
CAPS.update({
 'ext1':'Fresh paired score effects for V5 on 48 test worlds. Effects against polished controls use 46 jointly admitted worlds. V4 and V5 scores tie; their effects against controls are identical. Intervals are descriptive 95% whole-world bootstraps.',
 'ext2':'V5 feature controls on the first 16 predeclared worlds with two repetitions. All 32 scheduled pairs per control remain in the outcome categories; ties and control wins are retained.',
 'ext3':'Fresh primary computation costs. Planner wall time and all continuous metric calls have separate units. Shared scene preparation is excluded; equal ceilings do not equalize actual computation.',
 'ext4':'Execution outcomes on 12 predeclared worlds per method and assistance setting. Bars use scheduled denominators. Assistance 0.5 denotes repeated velocity blending, not half force or unassisted locomotion.',
 'ext5':'Budget sensitivity on the first eight fresh worlds. Positive paired score effects favor V5. Short-budget phases have one repetition; the 2 s subset has two. Joint-admission populations can change with budget.'})
ALGS['v5']=('Adaptive search candidate, evaluated without guaranteed improvement',[
 'Input: common map, limits, timer and candidate cap.',
 'Try an exact collision-checked direct connection.',
 'If feasible and within the declared model bound gap:',
 '  Return the registered direct incumbent.',
 'Otherwise allocate seed time from direct visibility.',
 'Run the fixed initial refiner and carry its count.',
 'Generate geometry landmarks within the node cap.',
 'Prioritize an internal search for a violated resource.',
 'Register candidates using unchanged feasible-first Q.',
 'Apply the common collision-checked local polishing.',
 'Return the best incumbent and all diagnostics.'])
original_named_table=named_table
def named_table(key):
 if not key.startswith('ext'):return original_named_table(key)
 if key=='extprotocol':table('Prospective extension phases',['Phase','Worlds','Methods','Repeats','Attempts'],[['Development, 2 profiles',8,4,1,64],['Fresh primary',48,4,2,384],['Feature controls',16,4,2,128],['0.5 and 1 s budgets',8,4,1,64],['80-candidate ceiling',16,4,1,64],['Assistance 1.0',12,4,1,48],['Assistance 0.5',12,4,1,48],['Total scheduled','-','-','-',800]],[1.18,.44,.53,.53,.65])
 elif key=='extmain':table('Fresh primary conditional means',['Method','Admitted','Mean Q','Plan s'],[[EN[r['method']],str(r['admitted'])+'/96',f"{r['mean_q']:.6f}",f"{r['mean_planning_s']:.4f}"] for r in EXT['primary']],[1.10,.56,.87,.80])
 elif key=='extpaired':table('Fresh V5 paired effects on jointly admitted worlds',['Baseline','Win','Tie','Loss','Mean %','95% interval %'],[[EN[r['baseline']],r['wins'],r['ties'],r['losses'],f"{r['mean_relative_percent']:.3f}",f"[{r['relative_ci95'][0]:.3f}, {r['relative_ci95'][1]:.3f}]"] for r in EXT['comparisons']],[1.02,.27,.27,.29,.52,.76])
 elif key=='extphysics':
  def val(x,places):return 'N/A' if x is None else f'{x:.{places}f}'
  table('Prospective assisted execution by condition',['Method / aid','Success / scheduled','Time s','Work J'],[[EN[r['method']]+' / '+str(r['assistance']),str(r['successful'])+'/'+str(r['scheduled']),val(r['mean_task_s'],3),val(r['mean_work_j'],1)] for r in EXT['physics']],[1.12,.72,.68,.81])
 else:raise ValueError(key)
'''
builder=builder.replace("label=p.add_run('\\t('+str(num)+')');label.font.italic=False", "if num==5:p.add_run().add_break()\n  label=p.add_run(('\\t\\t' if num==5 else '\\t')+'('+str(num)+')');label.font.italic=False")
builder=builder.replace('# Build scientific body from inspectable text, replacing only explicit slots.',extra+'\n# Build scientific body from inspectable text, replacing only explicit slots.')
(B/'source/build_manuscript.py').write_text(builder)
contract=(OLD/'artifact.md').read_text().replace(str(OLD/'template'),str(B/'template'))
contract+='\n## Authorized extension\nRetain all complete V4 sections and evidence. Add Section VII prospective validation, renumber discussion and conclusion to VIII and IX, update abstract, introduction, data availability and affected limitations. Add five scientific figures, four native tables and one algorithm using the same source-derived roles. Preserve 1,232 original attempts and distinguish 800 new attempts from 48 fresh independent test worlds. V5 is an evaluated candidate rather than a demonstrated improvement over V4.\n'
(B/'artifact.md').write_text(contract)
print(json.dumps({'source_words':len(text.split()),'abstract_words':len(abstract.split()),'extension_audit':audit['state']}))
