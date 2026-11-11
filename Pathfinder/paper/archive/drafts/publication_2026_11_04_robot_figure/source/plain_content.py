"""Self-contained prose and displays; no reader dependence on local evidence files."""
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

def rewrite(B,texts,tables,figures):
    texts['ABSTRACT']=('This study compares six route-planning configurations for a simulated six-legged robot. Each route must clear obstacles and meet a deadline, a nominal battery limit and a terrain-exposure limit. Eight development maps select the planner settings, and 32 main-test maps provide three repetitions per method, giving 640 planning attempts in total. The complete planner, V4, accepts 93 of 96 main-test attempts; a coordinate-based particle swarm planner, PSO-C, accepts 94. On routes accepted by both, V4 has a mean paired-map score improvement of 0.690%, a zero median and a descriptive 95% bootstrap interval of [−0.255, 2.312]%. The interval includes zero. Removing final local route adjustment reduces acceptance to 90 attempts. Removing landmark search retains 93 and reduces mean search time from 0.376 to 0.196 s. In four separate motion missions, full and half-scale body assistance each complete all missions; zero assistance completes none within 180 s. The assisted runs detect no foot-ground contact under the six-foot contact test. The results quantify planning differences and dependence on direct body assistance in the specified simulator. All battery costs are model outputs, with no physical or electrical validation.')
    texts['FRESH_RESULTS']=('All 640 planning attempts finish without a recorded trial error. The default profile is selected for every base method. In the main test, V4, PSO-P, ACO-P and V4 noL each accept 93/96 attempts. PSO-C accepts 94/96, and V4 noP accepts 90/96. Every rejected main-test attempt fails a resource requirement. Table 2 and Figure 2 report these acceptance counts. Mean search time is 0.376 s for V4 and 0.731 s for PSO-C; the fastest mean is 0.196 s for V4 noL.')
    texts['PAIRED_RESULTS']=('Against PSO-C, V4 produces a lower score on 33 paired accepted attempts, a tied score on 27 and a higher score on 33. PSO-C alone accepts one attempt, V4 alone accepts none, and both reject two. The mean of the map-level score differences is 0.690%, with a median of zero and a descriptive 95% interval of [−0.255, 2.312]%. Differences across the 31 paired maps range from −1.718% to 23.202%; five maps exceed the descriptive 0.5% improvement reference.\n\n'
    'V4 has mean paired score improvements of 0.929% against PSO-P, 0.921% against ACO-P, 0.924% against V4 noL and 0.794% against V4 noP. The first two comparisons both have zero medians. Against V4 noL, V4 has 27 lower-score pairs, 57 ties and nine higher-score pairs. Against V4 noP, it has 57 lower-score pairs, 33 ties and no higher-score pairs, plus three attempts accepted only by complete V4. Table 3 and Figure 3 summarize the paired-map means and intervals.')
    texts['FAMILY_RESULTS']=('All resource rejections in the main test occur in corridor maps. Open, clutter and rough maps each give 24/24 accepted attempts for every method. In corridor maps, V4, PSO-P, ACO-P and V4 noL each accept 21/24 attempts; PSO-C accepts 22/24 and V4 noP accepts 18/24. Table 4 locates both PSO-C’s additional acceptance and the three acceptances lost after removing final local adjustment in the corridor group.')
    texts['COMPUTE_RESULTS']=('PSO-C reaches the 240-route evaluation limit on 84/96 attempts. None of the other methods reaches it. Median evaluation counts are 33 for V4, 46 for PSO-P, 32.5 for ACO-P, 240 for PSO-C, 21 for V4 noL and five for V4 noP. Table 5 gives median and maximum search times together with these counts. Median geometric-clearance checks are 1,033 for V4, 2,142.5 for PSO-C and 146.5 for V4 noL. Shared preparation takes a median of 0.715 s and a maximum of 0.895 s per main-test map, outside the individual search timers.')
    texts['SENSITIVITY_RESULTS']=('Figure 4 shows every paired-map score difference against PSO-C. Map 24 has the largest positive difference, 23.202%. Leaving this map out changes the mean of the remaining paired maps from 0.690% to −0.060%. Table 6 reports the range of means obtained by leaving out each map in turn. Leaving out the largest positive map gives means of 0.187% against PSO-P, 0.178% against ACO-P and 0.182% against V4 noL. Against V4 noP, all omission means stay positive, ranging from 0.682% to 0.822%.')
    texts['PROBE_RESULTS']=('Full and half-scale body assistance each complete four of four missions. Zero assistance completes none of the four missions, both with gravity compensation enabled and with compensation verified as zero. Every unfinished mission reaches the 180 s time limit. Table 8 uses GC for leg-body gravity compensation. Completion covers the destination and return to the station; it is separate from planning acceptance.')
    texts['REPLAY_DETAIL']=('With full assistance, whole-mission distances range from 34.71 to 42.83 m, and elapsed times range from 62.85 to 89.63 s. With half-scale assistance, distances range from 34.75 to 42.91 m and times from 62.83 to 89.66 s. Each completed time includes eight seconds of station service. With zero assistance and compensation enabled, body displacement totals 0.324–0.326 m by the timeout. With zero assistance and compensation disabled, it totals 0.376–0.381 m. Figure 6 shows all four mission distances in each condition.\n\n'
    'Every full- and half-scale assisted run has zero detected foot contact at every sampled physics step. Their mean contact count is zero and their no-contact percentage is 100%. Table 9 gives the contact ranges across the four missions in every condition. The largest body tilt in the assisted runs is below 0.410 degrees, while the controller directly corrects roll and pitch. These are observations of the assisted model under the contact and orientation definitions in Section 5.4.')
    texts['CONCLUSION_RESULTS']=('In the 32-map main test, V4 accepts 93/96 attempts and PSO-C accepts 94/96. V4’s paired mean score improvement against PSO-C is 0.690%, with a zero median and a descriptive interval that includes zero. The test does not establish a lower average score for V4 against that control. Final local adjustment raises acceptance from 90 to 93 attempts. Landmark search retains the same acceptance count, with higher recorded computation and a 0.924% paired mean score improvement over its removal.')
    # Captions define their populations without relying on external records.
    captions={
      'TABLE_MODEL':'Table 1. Mass and joint settings of the two robot descriptions.',
      'TABLE_PRIMARY':'Table 2. Accepted main-test routes and mean search time.',
      'TABLE_PAIRED':'Table 3. Paired score differences favoring V4; n is the number of paired maps.',
      'TABLE_FAMILY':'Table 4. Accepted attempts out of 24 for each map type.',
      'TABLE_COMPUTE':'Table 5. Search time and evaluated routes over 96 attempts.',
      'TABLE_SENSITIVITY':'Table 6. Mean score differences after leaving out one paired map.',
      'TABLE_PROBE':'Table 8. Completed missions and timeouts under body assistance.',
      'TABLE_CONTACT':'Table 9. Contact-measurement ranges across four missions.'}
    for k,caption in captions.items():tables[k]=(caption,tables[k][1])
    for key in ['TABLE_PROBE','TABLE_CONTACT']:
        for row in tables[key][1][1:]:
            row[0]=row[0].replace('Blend + GC','Half + GC')
    tables['TABLE_PRIMARY'][1][0]=['Method','Accepted / 96','Mean time (s)']
    tables['TABLE_MODEL'][1][0]=['Parameter','Imported model','MuJoCo model']
    tables['TABLE_MODEL'][1][-1]=['Added parts','No wheel joints','Wheels and scanner']
    tables['TABLE_PAIRED'][1][0]=['Control','n','Mean (%)','95% interval (%)']
    figures['FIG_MODEL']=('primary_world.png','Figure 1. Map 1, repetition 0. Circle: start; star: goal; black: obstacles; amber: terrain. Routes overlap.')
    figures['FIG_PRIMARY']=('fresh_admission.png','Figure 2. Accepted main-test attempts out of 96 per method.')
    figures['FIG_EFFECTS']=('fresh_effects.png','Figure 3. Paired-map mean score differences and descriptive 95% bootstrap intervals. Positive values favor V4.')
    figures['FIG_DISTRIBUTION']=('world_distribution.png','Figure 4. Score difference against PSO-C on each paired map, averaged over jointly accepted repetitions. Positive values favor V4. All points remain in the primary mean.')
    figures['FIG_REPLAY']=('replay_distance.png','Figure 6. Whole-mission distance for four missions in each assistance condition. Points overlap when distances are similar. GC means leg-body gravity compensation.')
    primary=json.loads((B/'raw_study/primary.json').read_text());case=primary['cases'][23];assert case['seed']==2140023
    group={m:sorted([r for r in primary['records'] if r['case_id']==case['id'] and r['method']==m],key=lambda r:r['repeat']) for m in ['proposed_v4','continuous_pso']}
    assert all(len(rows)==3 and all(r['plan']['admissible'] for r in rows) for rows in group.values())
    means={m:{**{k:float(np.mean([r['plan']['metrics'][k] for r in rows])) for k in ['distance_m','estimated_seconds','energy_percent','terrain_exposure']},'quality_score':float(np.mean([r['plan']['quality_score'] for r in rows]))} for m,rows in group.items()}
    metric_rows=[('Distance (m)','distance_m'),('Time (s)','estimated_seconds'),('Battery (points)','energy_percent'),('Exposure','terrain_exposure'),('Score Q','quality_score')]
    tables['TABLE_CASE']=('Table 7. Mean route metrics on map 24 over three repetitions.',[['Metric','V4','PSO-C']]+[[label]+[f"{means[m][key]:.3f}" for m in group] for label,key in metric_rows])
    texts['CASE_RESULTS']=('Map 24 is a corridor map with seed 2140023. The start is (−7.75, 10.75) m and the destination is (−7.50, −8.75) m. The deadline is 110 s, available nominal battery is 85%, and the exposure limit is 20. The return-route battery estimate is 11.682 percentage points. Both methods accept all three repetitions. Table 7 compares the mean returned route metrics.\n\n'
    f"V4 returns the same route in all three repetitions, with distance {means['proposed_v4']['distance_m']:.3f} m and score {means['proposed_v4']['quality_score']:.3f}. PSO-C’s mean route distance is {means['continuous_pso']['distance_m']:.3f} m and mean score is {means['continuous_pso']['quality_score']:.3f}. V4 has lower distance, predicted time, nominal battery use and terrain exposure in each paired repetition. Because all four weights in equation (1) are positive, these differences all reduce Q. Figure 5 shows the routes from repetition zero: the PSO-C route takes a wider detour to the west. This observed route difference accounts for the lower score in that repetition; it does not identify a unique cause inside the search algorithm.")
    fig,ax=plt.subplots(figsize=(3.1,3.25))
    for region in case['world']['patches']:
        x0,x1,y0,y1=region['bounds'];ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,facecolor='#dfb76e',alpha=.45,edgecolor='none'))
    for o in case['world']['obstacles']:
        ax.add_patch(Rectangle((o['x']-o['sx'],o['y']-o['sy']),2*o['sx'],2*o['sy'],facecolor='#393939'))
    for method,color,ls,width in [('proposed_v4','#17686f','-',2.5),('continuous_pso','#a64b16','--',1.3)]:
        xy=np.array(group[method][0]['plan']['points']);ax.plot(xy[:,0],xy[:,1],ls,color=color,linewidth=width,label='V4' if method=='proposed_v4' else 'PSO-C')
    ax.scatter(*case['start'],marker='o',color='black',s=24,zorder=5);ax.scatter(*case['goal'],marker='*',color='black',s=55,zorder=5)
    ax.set(xlim=(-24,24),ylim=(-24,24),xlabel='x (m)',ylabel='y (m)');ax.set_aspect('equal');ax.legend(loc='lower right',frameon=False);ax.grid(alpha=.15);fig.tight_layout();fig.savefig(B/'figures/map24_routes.png',dpi=400);fig.savefig(B/'figures/map24_routes.pdf');plt.close(fig)
    figures['FIG_CASE']=('map24_routes.png','Figure 5. Routes on corridor map 24, repetition 0. The PSO-C route passes farther west than the V4 route. The circle and star mark start and destination; amber regions mark terrain patches.')
    (B/'results/map24_analysis.json').write_text(json.dumps(dict(case=case['id'],seed=case['seed'],selection='Largest positive paired-map effect against PSO-C; post hoc illustration',means=means,repetitions=3,all_six_routes_accepted=True,plotted_repeat=0),indent=2)+'\n')
    # Plot wording uses the same defined terms as the narrative.
    # Rebuild the admission chart rather than editing a raster label.
    summary=json.loads((B/'results/study_analysis.json').read_text())['primary_summary'];names={'proposed_v4':'V4','pso_polished':'PSO-P','aco_polished':'ACO-P','continuous_pso':'PSO-C','proposed_v4_no_landmarks':'V4 noL','proposed_v4_no_polish':'V4 noP'}
    lookup={r['method']:r for r in summary};values=[lookup[m]['admitted'] for m in names]
    fig,ax=plt.subplots(figsize=(3.1,2.3));bars=ax.barh(range(6),values,color=['#17686f']+['#7c96ae']*5);ax.set_yticks(range(6),list(names.values()));ax.invert_yaxis();ax.set_xlim(0,108);ax.set_xlabel('Accepted / 96 attempts')
    for bar,value in zip(bars,values):ax.text(value+1,bar.get_y()+bar.get_height()/2,str(value),va='center')
    fig.tight_layout();fig.savefig(B/'figures/fresh_admission.png',dpi=400);fig.savefig(B/'figures/fresh_admission.pdf');plt.close(fig)
    import csv
    effects=list(csv.DictReader((B/'results/world_effects.csv').open()))
    rows=sorted([r for r in effects if r['baseline']=='continuous_pso'],key=lambda r:r['world'])
    fig,ax=plt.subplots(figsize=(3.1,3.05));ax.scatter([int(r['world'].split('_')[-1]) for r in rows],[float(r['relative_percent']) for r in rows],s=18,color='#17686f');ax.axhline(0,color='grey',lw=.8)
    ax.set(xlabel='Main-test map',ylabel='V4 score improvement (%)',xticks=[1,8,16,24,32]);ax.grid(alpha=.15);fig.tight_layout();fig.savefig(B/'figures/world_distribution.png',dpi=400);fig.savefig(B/'figures/world_distribution.pdf');plt.close(fig)
    probe=json.loads((B/'results/realism_probe.json').read_text());corrected=json.loads((B/'results/corrected_gravity_probe.json').read_text())
    realized=[r for r in probe['records'] if r['gravity_compensation']]+corrected['records']
    fig,ax=plt.subplots(figsize=(3.1,2.9))
    for i,(scale,gc,color) in enumerate([(1.,True,'#17686f'),(.5,True,'#4f7e99'),(0.,True,'#a96b35'),(0.,False,'#6e6262')]):
        rows=[r for r in realized if r['assistance']==scale and r['gravity_compensation']==gc]
        ax.scatter(np.arange(4)*.045+i-.0675,[r['execution']['distance_m'] for r in rows],s=24,color=color,zorder=3)
    ax.set(xticks=range(4),xticklabels=['Full\n+ GC','Half\n+ GC','Zero\n+ GC','Zero\nno GC'],ylabel='Mission distance (m)',ylim=(-2,47));ax.grid(axis='y',alpha=.2);fig.tight_layout();fig.savefig(B/'figures/replay_distance.png',dpi=400);fig.savefig(B/'figures/replay_distance.pdf');plt.close(fig)
    assert len(texts['ABSTRACT'].split())<=250

