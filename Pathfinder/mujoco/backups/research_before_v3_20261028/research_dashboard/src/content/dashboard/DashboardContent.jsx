import React,{useState} from 'react';
import {DataComponent,DataTable,Dropdown,EvidenceChart,SectionHeader,SortableItem,SortableRegion,useDataApp} from '../../data-app-public.jsx';
import './research.css';
const short={b1_distance:'B1 Distance',b2_terrain:'B2 Terrain',b3_energy:'B3 Energy',b4_weighted:'B4 Weighted',pso:'B5 PSO',aco:'B6 ACO',b7_greedy:'B7 Greedy',proposed_v1:'Previous proposal',proposed:'Proposed hybrid'};
const color={b1_distance:'var(--chart-1)',b2_terrain:'var(--chart-2)',b3_energy:'var(--chart-3)',b4_weighted:'var(--chart-4)',pso:'var(--chart-6)',aco:'var(--chart-7)',b7_greedy:'var(--chart-8)',proposed_v1:'var(--chart-2)',proposed:'var(--chart-5)'};
const mean=(r,k)=>{const v=r.map(x=>x[k]).filter(x=>x!==null&&Number.isFinite(x));return v.length?v.reduce((a,b)=>a+b,0)/v.length:null;};
const fmt=v=>v==null?'Unavailable':Number(v).toFixed(2);
function Route({row,map,label,tone}){
 const route=JSON.parse(row?.route_json||'[]'),trace=JSON.parse(row?.trace_json||'[]');
 const bounds=map.bounds||[-48,48],size=bounds[1]-bounds[0];
 return <div className="lab-route"><h3>{label}</h3><p>{row?.status||'No trial'}</p>
 <svg viewBox={`${bounds[0]} ${bounds[0]} ${size} ${size}`} role="img" aria-label={`${label} actual simulated map and route in metres`}><title>{label} plan and measured mission trail</title>
 <rect x={bounds[0]} y={bounds[0]} width={size} height={size} fill="var(--surface)" stroke="var(--border)" strokeWidth=".3"/>
 <g transform="scale(1,-1)">{(map.obstacles||[]).map((b,i)=><rect key={i} x={b[0][0]} y={b[0][1]} width={b[1][0]-b[0][0]} height={b[1][1]-b[0][1]} fill="var(--secondary)" opacity=".28"/>)}
 {route.length>0&&<polyline points={route.map(p=>p.join(',')).join(' ')} fill="none" stroke={tone} strokeWidth=".65"/>}
 {trace.length>0&&<polyline points={trace.map(p=>p.xy.join(',')).join(' ')} fill="none" stroke={tone} strokeWidth=".4" strokeDasharray="1 1"/>}
 {map.start&&<circle cx={map.start[0]} cy={map.start[1]} r="1.1" fill="var(--text)"><title>Start</title></circle>}
 {map.goal&&<rect x={map.goal[0]-.9} y={map.goal[1]-.9} width="1.8" height="1.8" fill="var(--text)"><title>Destination</title></rect>}</g></svg>
 <p>{size} × {size} m · circle start · square destination · solid plan · dashed measured mission</p></div>;
}
export function DashboardContent(){
 const {reviewedRows,snapshot}=useDataApp(),all=reviewedRows('trials'),maps=reviewedRows('cases');
 const [selected,setSelected]=useState('all'),[baseline,setBaseline]=useState('pso'),[repetition,setRepetition]=useState('all');
 const cases=[...new Set(all.map(r=>r.case))],active=selected==='all'?(all.find(r=>r.executed)?.case||cases[0]):selected;
 const rows=all.filter(r=>(selected==='all'||r.case===selected)&&(repetition==='all'||String(r.repetition||1)===repetition)),methods=snapshot.research?.methods||Object.keys(short);
 const names={...short,proposed:snapshot.research?.algorithm_version==='common_seed_portfolio_v2'?'Proposed hybrid':(all.find(r=>r.method==='proposed')?.methodLabel||'Saved proposal')};
 const repetitions=[...new Set(all.map(r=>String(r.repetition||1)))].sort((a,b)=>Number(a)-Number(b));
 const compared=methods.includes(baseline)?baseline:methods.find(m=>m!=='proposed');
 const summaries=methods.map(method=>{const g=rows.filter(r=>r.method===method),ok=g.filter(r=>r.admissible),good=g.filter(r=>r.success);
 return {method,methodLabel:names[method],attempts:g.length,admitted:ok.length,successes:snapshot.research?.execute?good.length:null,
 successRate:g.length&&snapshot.research?.execute?good.length/g.length:null,
 admissionRate:g.length?ok.length/g.length:null,quality_score:mean(ok,'quality_score'),
 planning_time_s:mean(g,'planning_time_s'),task_time_s:mean(good,'task_time_s'),mission_work_j:mean(good,'mission_work_j'),
 mission_energy_percent:mean(good,'mission_energy_percent'),max_tilt_deg:mean(good,'max_tilt_deg'),charging_stops:mean(good,'charging_stops'),modeled_swaps:mean(good,'modeled_swaps')};});
 const metrics=[['admission','Plans meeting all resource limits','admissionRate','Admission rate'],['quality','Common score of admitted routes','quality_score','Lower is better'],
 ['success','Mission success including all attempts','successRate','Success rate'],['planning','Planning time','planning_time_s','Wall seconds'],
 ['time','Time to destination on successful missions','task_time_s','Seconds'],['energy','Modeled battery use on successful missions','mission_energy_percent','Percentage points including return'],
 ['work','Positive actuator work on successful missions','mission_work_j','Mechanical joules including return'],['tilt','Maximum body tilt on successful missions','max_tilt_deg','Degrees in assisted model'],
 ['charge','Charging stops on successful missions','charging_stops','Mean stops'],['swap','Modeled replacements on successful missions','modeled_swaps','Mean modeled events']];
 const shownRepeat=repetition==='all'?(rows.find(r=>r.case===active)?.repetition||1):Number(repetition);
 const scenarioRows=rows.filter(r=>r.case===active&&(r.repetition||1)===shownRepeat),map=JSON.parse(maps.find(r=>r.case===active)?.map_json||'{}');
 const convergence=snapshot.queries?.convergence?reviewedRows('convergence').filter(r=>r.case===active&&r.repetition===shownRepeat):[];
 return <article className="lab-dashboard"><div className="lab-context"><Dropdown label="Scenario" showLabel value={selected} choices={['all',...cases]} choiceLabels={{all:'All scenarios'}} onChange={setSelected}/>
 <Dropdown label="Repetition" showLabel value={repetition} choices={['all',...repetitions]} choiceLabels={{all:'All repetitions'}} onChange={setRepetition}/>
 <span>{snapshot.research?.suite} · {snapshot.research?.execute?'physics executed':'planning only'} · {snapshot.research?.locomotion?.replaceAll('_',' ')} · {snapshot.research?.resolution_m} m grid · {snapshot.research?.state}</span><a href="http://127.0.0.1:8771">Experiment console</a></div>
 <p className="lab-note" data-editable-id="scope">Paired comparisons on one underlying scene. PSO and ACO refine a charged safe A* seed; all optimizers use the same resource checks and total budget. Repeated seeds are not independent maps. Rejected plans remain in denominators. Cost averages may cover different scenarios; filter for paired inspection. Mechanical work is not battery energy, and assisted tilt does not establish real robot stability.</p>
 <p className="lab-note" data-editable-id="score-definition">Common route score = distance/50 + predicted seconds/90 + battery percentage points/30 + 0.25 × terrain exposure/20. Smaller is better among routes that meet all limits.</p>
 {snapshot.research?.study&&<p className="lab-note" data-reviewed-rows>Study stage: {snapshot.research.study.phase}. {snapshot.research.layout_count} sampled task/obstacle layouts × {snapshot.research.repeats} repetitions per method. Parameters were selected on separate development cases and frozen before held-out testing. Every layout uses the same base terrain. Planning admission is not measured mission success.</p>}
 {snapshot.queries?.paired_comparison&&<>
 <SectionHeader id="paired-heading" title="Proposed versus each baseline on matching test cases"/>
 <p className="lab-note" data-editable-id="paired-scope">Full held-out set; these counts do not change with the filters above. Wins, ties and losses compare common scores when both plans meet the limits. The remaining columns keep rejected cases visible. A win here concerns the modeled route score, not measured robot performance.</p>
 <DataComponent id="paired-comparison" queryId="paired_comparison" title="Paired held-out outcomes" kind="table" variant="card" sourceRows={reviewedRows('paired_comparison')} displayRows={reviewedRows('paired_comparison')}><DataTable rows={reviewedRows('paired_comparison')} searchable={false} columns={[
 {field:'baseline',label:'Baseline'},{field:'wins',label:'Proposed wins'},{field:'ties',label:'Ties'},{field:'losses',label:'Proposed losses'},
 {field:'proposed_only_admitted',label:'Only proposed admitted'},{field:'baseline_only_admitted',label:'Only baseline admitted'},{field:'both_rejected',label:'Neither admitted'}]}/></DataComponent>
 </>}
 <SectionHeader id="outcomes-heading" title="Completion and resource use"/>
 <SortableRegion id="research:charts" variant="canvas" columns={12} spacing="standard" rows={metrics.filter((_,i)=>i%2===0).map((m,i)=>({id:`research:row${i}`,items:[m[0],metrics[i*2+1][0]]}))}>
 {metrics.map(([id,title,field,unit])=><SortableItem key={id} id={id} label={title} kind="chart" span={6}><EvidenceChart id={id} queryId="trials" title={title} variant="card" rows={summaries} sourceRows={rows} height={250}
 spec={{type:'horizontalBar',x:'methodLabel',y:field,series:'methodLabel',colors:Object.fromEntries(methods.map(m=>[names[m],color[m]])),startAtZero:true,stackable:false,showLegend:false,valueDecimals:3,xLabel:unit,showYAxisLabel:false}}/></SortableItem>)}
 </SortableRegion>
 <div className="lab-heading"><SectionHeader id="tradeoffs-heading" title="Predicted route trade offs"/></div>
 <EvidenceChart id="tradeoffs" queryId="trials" title="Predicted destination time versus modeled energy" variant="card" rows={rows.filter(r=>r.predicted_time_s!==null)} sourceRows={rows} height={340}
 spec={{type:'scatter',x:'predicted_time_s',y:'predicted_energy_percent',series:'methodLabel',xLabel:'Predicted destination seconds',yLabel:'Predicted battery percentage points',stackable:false,valueDecimals:2}}/>
 <div className="lab-heading"><SectionHeader id="convergence-heading" title={`Observed search progress for ${active||'no scenario'} · repetition ${shownRepeat}`}/></div>
 {convergence.length>0?<EvidenceChart id="search-progress" queryId="convergence" title="Best feasible score found during planning" variant="card" rows={convergence} sourceRows={convergence} height={280}
 spec={{type:'line',x:'elapsed_s',y:'quality_score',series:'methodLabel',xLabel:'Elapsed planning wall seconds',yLabel:'Common route score',stackable:false,valueDecimals:3}}/>:<p className="lab-note">No feasible optimization progress was recorded for this scenario and repetition.</p>}
 <div className="lab-heading"><SectionHeader id="routes-heading" title={`Side by side routes for ${active||'no scenario'} · repetition ${shownRepeat}`}/><Dropdown label="Baseline" showLabel value={compared} choices={methods.filter(m=>m!=='proposed')} choiceLabels={names} onChange={setBaseline}/></div>
 <DataComponent id="routes" queryId="trials" queryIds={['trials','cases']} title="Plans and measured mission trails" kind="custom" variant="card" displayRows={scenarioRows} sourceRowsByQuery={{trials:scenarioRows,cases:maps.filter(r=>r.case===active)}}>
 <div className="lab-route-grid" data-reviewed-rows><Route row={scenarioRows.find(r=>r.method===compared)} map={map} label={names[compared]} tone={color[compared]}/><Route row={scenarioRows.find(r=>r.method==='proposed')} map={map} label={scenarioRows.find(r=>r.method==='proposed')?.methodLabel||names.proposed} tone={color.proposed}/></div></DataComponent>
 <div className="lab-heading"><SectionHeader id="denominators-heading" title="Comparison denominators"/></div>
 <DataComponent id="method-summary" queryId="trials" title="Method summary" kind="table" variant="card" displayRows={summaries} sourceRows={rows}><DataTable rows={summaries} searchable={false} columns={[
 {field:'methodLabel',label:'Method'},{field:'attempts',label:'Attempts'},{field:'admitted',label:'Admitted'},{field:'successes',label:'Succeeded'},{field:'successRate',label:'Success',presentation:'percent'},
 {field:'mission_work_j',label:'Work J',renderCell:fmt},{field:'max_tilt_deg',label:'Tilt deg',renderCell:fmt}]}/></DataComponent>
 <div className="lab-heading"><SectionHeader id="attempts-heading" title="Inspect every attempt"/></div>
 <DataComponent id="attempts" queryId="trials" title="Trial records including rejected plans" kind="table" variant="card" displayRows={rows} sourceRows={rows}><DataTable rows={rows} columns={[
 {field:'case',label:'Scenario'},{field:'repetition',label:'Repeat'},{field:'seed',label:'Seed'},{field:'methodLabel',label:'Method'},{field:'status',label:'Outcome',presentation:'status'},{field:'reason',label:'Why accepted or rejected'},{field:'quality_score',label:'Route score',renderCell:fmt},
 {field:'predicted_time_s',label:'Predicted s',renderCell:fmt},{field:'task_time_s',label:'Measured s',renderCell:fmt},{field:'required_battery_percent',label:'Required battery %',renderCell:fmt}]}/></DataComponent>
 {snapshot.queries?.gait_comparison&&<><div className="lab-heading"><SectionHeader id="gait-heading" title="Separate gait calibration experiment"/></div>
 <p className="lab-note" data-editable-id="gait-scope">Original timing versus the best eligible setting selected on these same tracks. This is calibration, with ten trials per terrain grade; scenario and repetition filters apply to planner trials only. Validate on new tracks before making a general improvement claim.</p>
 <EvidenceChart id="gait-work" queryId="gait_comparison" title="Measured positive leg work per metre" variant="card" rows={reviewedRows('gait_comparison')} sourceRows={reviewedRows('gait_comparison')} height={300}
 spec={{type:'bar',x:'terrain',y:'default_work_j_m',fields:['default_work_j_m','selected_work_j_m'],startAtZero:true,stackable:false,yLabel:'Mechanical joules per metre',legend:{labels:{default_work_j_m:'Original gait',selected_work_j_m:'Selected calibration setting'}},valueDecimals:2}}/>
 </>}</article>;
}
