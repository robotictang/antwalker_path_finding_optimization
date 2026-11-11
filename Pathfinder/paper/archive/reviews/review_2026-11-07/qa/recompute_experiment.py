"""Independent arithmetic audit of stored experiment records; no simulations run."""
from pathlib import Path
from collections import Counter, defaultdict
import hashlib, json, math, statistics
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
B = ROOT / "publication_2026_11_05_revised"
names = ["development_default", "development_alternative", "primary"]
phases = {name: json.loads((B / "raw_study" / (name + ".json")).read_text()) for name in names}
report = {"scope": "Recomputed stored-record arithmetic, not new physics or hardware validation", "files": {}}

def grade_at(points, patches, margin=0):
    answer=np.zeros(np.shape(points)[:-1], dtype=int)
    for patch in patches:
        x0,x1,y0,y1=patch["bounds"]
        inside=(points[...,0]>=x0-margin)&(points[...,0]<=x1+margin)&(points[...,1]>=y0-margin)&(points[...,1]<=y1+margin)
        answer=np.maximum(answer,np.where(inside,patch["grade"],0))
    return answer

def ground_at(points, world):
    height=np.where(grade_at(points,world["patches"])>0,.02,0.)
    for tile in world["tiles"]:
        inside=(abs(points[...,0]-tile["x"])<=tile["sx"])&(abs(points[...,1]-tile["y"])<=tile["sy"])
        height=np.maximum(height,np.where(inside,tile["height"],0.))
    return height

def difficulty_grid(world):
    xy=-24+np.indices((193,193)).transpose(1,2,0)*.25
    h=np.array([ground_at(xy+np.array([dx,dy]),world) for dx in [-1.82,0,1.82] for dy in [-1.82,0,1.82]])
    gx,gy=np.gradient(h.mean(axis=0),.25)
    slope=np.arctan(np.hypot(gx,gy))
    softness=np.take([0,.25,.60],grade_at(xy,world["patches"],1.1))
    return np.clip(.25*(slope/.25+(h.max(axis=0)-h.min(axis=0))/.12+h.std(axis=0)/.04+softness),0,2)

def independent_metrics(points, world, difficulty):
    points=np.array(points);integrated=[points[0]]
    for a,b in zip(points,points[1:]):
        d=b-a;events=[0.,1.]
        for patch in world["patches"]:
            x0,x1,y0,y1=patch["bounds"]
            for axis,edges in [(0,[x0-1.1,x1+1.1]),(1,[y0-1.1,y1+1.1])]:
                if abs(d[axis])>1e-10:
                    events.extend(t for edge in edges if 0<(t:=(edge-a[axis])/d[axis])<1)
        for t in sorted(set(events))[1:]:
            point=a+t*d
            if np.linalg.norm(point-integrated[-1])>1e-9:integrated.append(point)
    if len(integrated)==1:integrated.append(integrated[0])
    integrated=np.array(integrated);d=np.diff(integrated,axis=0);lengths=np.linalg.norm(d,axis=1)
    headings=np.arctan2(d[:,1],d[:,0])[lengths>1e-8]
    turn=float(np.abs((np.diff(np.r_[math.pi/2,headings])+math.pi)%(2*math.pi)-math.pi).sum())
    grade=grade_at((integrated[1:]+integrated[:-1])/2,world["patches"],1.1)
    speeds=np.take([.75,.65,.38],grade)
    distance=float(lengths.sum());seconds=turn+float((lengths/speeds).sum())+(.6 if distance>1e-8 else 0)
    energy=.7*distance+.015*seconds+.08*turn+(.1 if distance>1e-8 else 0)
    exposure=0
    for a,b in zip(points,points[1:]):
        length=np.linalg.norm(b-a);n=max(2,int(math.ceil(length/.125))+1)
        cells=np.clip(np.rint((np.linspace(a,b,n)+24)/.25).astype(int),0,192)
        exposure+=length*float(difficulty[cells[:,0],cells[:,1]].mean())
    return dict(distance_m=distance,estimated_seconds=seconds,energy_percent=energy,terrain_exposure=exposure)

def point_to_segment(p,a,b):
    d=b-a;t=np.clip(np.dot(p-a,d)/max(np.dot(d,d),1e-20),0,1)
    return float(np.linalg.norm(p-(a+t*d)))

def cross(a,b):return a[0]*b[1]-a[1]*b[0]

def geometry_clear(points,world):
    points=np.array(points)
    if np.any(points < -24) or np.any(points > 24):return False
    for obstacle in world["obstacles"]:
        x,y,sx,sy=(obstacle[k] for k in ["x","y","sx","sy"])
        if any(x-sx<=point[0]<=x+sx and y-sy<=point[1]<=y+sy for point in points):return False
        corners=[np.array(p) for p in [(x-sx,y-sy),(x-sx,y+sy),(x+sx,y+sy),(x+sx,y-sy)]]
        for a,b in zip(points,points[1:]):
            for c,d in zip(corners,corners[1:]+corners[:1]):
                denom=cross(b-a,d-c)
                if abs(denom)>1e-14:
                    u=cross(c-a,d-c)/denom;v=cross(c-a,b-a)/denom
                    if 0<=u<=1 and 0<=v<=1:return False
                if min(point_to_segment(a,c,d),point_to_segment(b,c,d),point_to_segment(c,a,b),point_to_segment(d,a,b))<=1.82+.12+.005:return False
    return True

difficulties={}
metric_cache={}
for name, p in phases.items():
    file = B / "raw_study" / (name + ".json")
    expected = {(c["id"], m, j) for c in p["cases"] for m in p["methods"] for j in range(p["repeats"])}
    keys = [(r["case_id"], r["method"], r["repeat"]) for r in p["records"]]
    scores, batteries, admissions, distances = [], [], [], []
    metric_errors=defaultdict(list);blocked=[]
    cases = {c["id"]: c for c in p["cases"]}
    for row in p["records"]:
        plan = row["plan"]
        m = plan.get("metrics")
        if m is None:
            continue
        c = cases[row["case_id"]]
        q = m["distance_m"] / 50 + m["estimated_seconds"] / 90 + m["energy_percent"] / 30 + m["terrain_exposure"] / 80
        required = 1.25 * (m["energy_percent"] + c["return_energy_percent"]) + 6
        admitted = (m["estimated_seconds"] <= c["deadline_s"] + 1e-8 and required <= c["battery_percent"] + 1e-8 and m["terrain_exposure"] <= c["risk_budget"] + 1e-8)
        points = np.array(plan["points"])
        distance = np.linalg.norm(np.diff(points, axis=0), axis=1).sum()
        scores.append(abs(q - plan["quality_score"]))
        batteries.append(abs(required - plan["required_battery_percent"]))
        admissions.append(admitted == plan["admissible"])
        distances.append(abs(distance - m["distance_m"]))
        key=(c["world_sha256"],tuple(map(tuple,points)))
        if c["world_sha256"] not in difficulties:difficulties[c["world_sha256"]]=difficulty_grid(c["world"])
        if key not in metric_cache:
            metric_cache[key]=independent_metrics(points,c["world"],difficulties[c["world_sha256"]])
            if not geometry_clear(points,c["world"]):blocked.append([row["case_id"],row["method"],row["repeat"]])
        for field,value in metric_cache[key].items():metric_errors[field].append(abs(value-m[field]))
    report["files"][name] = dict(path=str(file.resolve()), sha256=hashlib.sha256(file.read_bytes()).hexdigest(), records=len(keys), expected=len(expected), unique_keys=len(set(keys)), expected_keys_match=set(keys)==expected, state=p["state"], statuses=dict(Counter(r["status"] for r in p["records"])), maximum_score_error=max(scores), maximum_required_battery_error=max(batteries), admission_matches=all(admissions), maximum_distance_error=max(distances), min_seed=min(c["seed"] for c in p["cases"]), max_seed=max(c["seed"] for c in p["cases"]))
    report["files"][name].update(independent_metric_max_errors={k:max(v) for k,v in metric_errors.items()}, blocked_unique_routes=blocked)

report["development_selection"] = {}
for method in phases["development_default"]["methods"]:
    values = {}
    for profile in ["default", "alternative"]:
        rows = [r for r in phases["development_" + profile]["records"] if r["method"] == method and r["plan"]["admissible"]]
        values[profile] = dict(accepted=len(rows), mean_q=statistics.mean(r["plan"]["quality_score"] for r in rows))
    chosen = min(values, key=lambda x: (-values[x]["accepted"], values[x]["mean_q"], x != "default"))
    report["development_selection"][method] = dict(profiles=values, chosen=chosen)

p = phases["primary"]
case_by_id = {c["id"]: c for c in p["cases"]}
ix = {(r["case_id"],r["repeat"],r["method"]):r["plan"] for r in p["records"]}
report["primary"] = []
for method in p["methods"]:
    rows = [r for r in p["records"] if r["method"] == method]
    plans = [r["plan"] for r in rows]
    report["primary"].append(dict(method=method, attempts=len(rows), accepted=sum(x["admissible"] for x in plans), mean_seconds=statistics.mean(x["planning_seconds"] for x in plans), median_seconds=statistics.median(x["planning_seconds"] for x in plans), max_seconds=max(x["planning_seconds"] for x in plans), median_evaluations=statistics.median(x["optimizer"]["fitness_evaluations"] for x in plans), at_240=sum(x["optimizer"]["fitness_evaluations"]==240 for x in plans), median_clearance_queries=statistics.median(x["optimizer"].get("visibility_checks",0) for x in plans), family_acceptance={family:sum(r["plan"]["admissible"] for r in rows if case_by_id[r["case_id"]]["world"]["family"]==family) for family in ["open","clutter","rough","corridor"]}, rejection_details=[dict(case=r["case_id"], repeat=r["repeat"], deadline_ok=r["plan"]["deadline_ok"], battery_ok=r["plan"]["battery_ok"], terrain_budget_ok=r["plan"]["terrain_budget_ok"]) for r in rows if not r["plan"]["admissible"]]))
report["shared_preparation"] = {field:dict(mean=statistics.mean(c[field] for c in p["cases"]), median=statistics.median(c[field] for c in p["cases"]), max=max(c[field] for c in p["cases"])) for field in ["total_preparation_seconds", "preparation_seconds"]}
report["paired"] = []
for control in p["methods"]:
    if control == "proposed_v4": continue
    counts=Counter(); effects={}
    for case in p["cases"]:
        v=[]
        for repeat in range(p["repeats"]):
            a=ix[case["id"], repeat, "proposed_v4"]; b=ix[case["id"],repeat,control]
            if a["admissible"] and b["admissible"]:
                delta=b["quality_score"]-a["quality_score"]
                counts["tie" if abs(delta)<=1e-8 else "CLRP_lower" if delta>0 else "CLRP_higher"] += 1
                v.append(100 * delta/b["quality_score"])
            else:
                counts["CLRP_only" if a["admissible"] else "control_only" if b["admissible"] else "both_rejected"] += 1
        if v: effects[case["id"]]=statistics.mean(v)
    values=np.array(list(effects.values())); rng=np.random.default_rng(41104)
    ci=np.percentile(rng.choice(values,size=(5000,len(values)),replace=True).mean(axis=1),[2.5,97.5])
    omissions=[statistics.mean([v for key,v in effects.items() if key != excluded]) for excluded in effects]
    report["paired"].append(dict(control=control,paired_maps=len(values),mean=statistics.mean(values),median=statistics.median(values),ci95=ci.tolist(),min=min(values),max=max(values),counts=dict(counts),leave_one_out_min=min(omissions),leave_one_out_max=max(omissions),without_map24=statistics.mean([v for key,v in effects.items() if key!="ij3ctest_24"]),map_effects=effects))
report["map24"]={}
for method in ["proposed_v4","continuous_pso"]:
    rows=[ix["ij3ctest_24",j,method] for j in range(3)]
    report["map24"][method] = {field:dict(mean=statistics.mean(row["metrics"][field] for row in rows), values=[row["metrics"][field] for row in rows]) for field in ["distance_m","estimated_seconds","energy_percent","terrain_exposure"]}
    report["map24"][method]["q"]=[row["quality_score"] for row in rows]

probe = json.loads((B/"results/realism_probe.json").read_text())
corrected=json.loads((B/"results/corrected_gravity_probe.json").read_text())
valid=[r for r in probe["records"] if r["gravity_compensation"]]+corrected["records"]
report["motion_conditions"]=[]
for condition in [(1.0,True),(.5,True),(0.,True),(0.,False)]:
    rows=[r for r in valid if (r["assistance"],r["gravity_compensation"])==condition]
    e=[r["execution"] for r in rows]
    report["motion_conditions"].append(dict(condition=list(condition),n=len(rows),completed=sum(x["success"] for x in e),outcomes=dict(Counter(x["outcome"] for x in e)),ranges={field:[min(x[field] for x in e),max(x[field] for x in e)] for field in ["distance_m","elapsed_s","mean_contact_feet","no_foot_contact_fraction","max_tilt_deg","physics_samples","service_seconds"]},realized_settings=[r.get("realized_settings") for r in rows] if not condition[1] else None))
probe_input=json.loads((B/"results/realism_probe_input_v6.json").read_text())
report["motion_inputs"]=[]
for c in probe_input["cases"][:4]:
    plan=next(r["plan"] for r in probe_input["records"] if r["case_id"]==c["id"] and r["repeat"]==0 and r["method"]=="proposed_v4")
    report["motion_inputs"].append(dict(case=c["id"],seed=c["seed"],family=c["world"]["family"],distance_m=plan["metrics"]["distance_m"],battery_percent=c["battery_percent"]))
snapshot=ROOT/"workbench/mujoco/outputs/research"/p["source_snapshot"]
report["source_snapshot"]=str(snapshot)
report["source_snapshot_mismatches"]=[name for name,sha in p["source_sha256"].items() if hashlib.sha256((snapshot/name).read_bytes()).hexdigest()!=sha]
report["independent_unique_routes_checked"]=len(metric_cache)
(OUT/"recomputed_experiment.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps({k:v for k,v in report.items() if k not in ["paired","map24"]},indent=2))
print(json.dumps({"paired":[{k:v for k,v in x.items() if k!="map_effects"} for x in report["paired"]],"map24":report["map24"]},indent=2))
