"""Independent checks for resumable search, procedural geometry and calibration guards."""
import csv,json,tempfile,time,unittest
from pathlib import Path
import numpy as np
import mujoco
import research.test_research as fixtures
from research.planning import ScalarSearchSession,scalar_search,plan,Limits
from research.worlds import Terrain,make_world,world_model,terrain_context,identity
from research.reference_validation import validate
from research.calibration import fit,write_template,validate_profile

class V3Tests(unittest.TestCase):
    def test_resuming_preserves_frontier_and_expansion_count(self):
        g=fixtures.ResearchTests().graph();a=np.array([1.,1.]);b=np.array([7.,6.]);end=time.perf_counter()+3
        session=ScalarSearchSession(g,a,b,[1,0,0,0],0)
        route,n,status=session.run_until(end,2)
        self.assertIsNone(route);self.assertEqual(status,'expansion_limit');self.assertEqual(n,2)
        route,m,status=session.run_until(end,10000)
        direct,total,expected=scalar_search(g,a,b,[1,0,0,0],0,end,10000)
        self.assertEqual(status,expected);self.assertEqual(n+m,total);np.testing.assert_allclose(route,direct)
    def test_world_heights_match_physical_geometry_and_restore_on_failure(self):
        import safe_navigation as nav
        import road_demo
        old=(nav.MAP_HALF_EXTENT,road_demo.ground_height)
        spec=make_world(1234,'rough');model=world_model(spec);terrain=Terrain(spec)
        data=mujoco.MjData(model);mujoco.mj_forward(model,data)
        with terrain_context(spec):
            navigator=nav.SafeNavigator(model,data,resolution=.25)
            for obstacle in spec['obstacles']:
                self.assertFalse(navigator.segment_clear(np.array([obstacle['x']-.1,obstacle['y']]),np.array([obstacle['x']+.1,obstacle['y']])))
        for i,t in enumerate(spec['tiles']):
            geom=model.geom(f'research_tile_{i}')
            self.assertAlmostEqual(model.geom_pos[geom.id,2]+model.geom_size[geom.id,2],t['height'])
            heights=[.02]+[q['height'] for q in spec['tiles'] if abs(q['x']-t['x'])<=q['sx'] and abs(q['y']-t['y'])<=q['sy']]
            self.assertAlmostEqual(float(terrain.ground_height([t['x'],t['y']])),max(heights))
        with self.assertRaises(RuntimeError):
            with terrain_context(spec):
                self.assertEqual(nav.MAP_HALF_EXTENT,24);raise RuntimeError('controlled failure')
        self.assertEqual(nav.MAP_HALF_EXTENT,old[0]);self.assertIs(road_demo.ground_height,old[1])
        self.assertEqual(identity(spec),identity(make_world(1234,'rough')))
        self.assertNotEqual(identity(spec),identity(make_world(1235,'rough')))
    def test_ablation_switches_and_feasibility(self):
        g=fixtures.ResearchTests().graph()
        for method,key in [('proposed_fixed','adaptive_seed_time'),('proposed_single','seed_portfolio'),('proposed_unpruned','resource_bound_pruning')]:
            r=plan(g,np.array([1.,1.]),np.array([6.,6.]),method,Limits(60,100,100,2),2.)
            self.assertFalse(r['optimizer']['parameters'][key]);self.assertTrue(r['admissible'])
    def test_small_corridors_match_exhaustive_reference(self):
        r=validate();self.assertEqual(r['state'],'passed');self.assertEqual(r['mismatches'],[])
    def test_external_fit_math_and_split_leak_guard_with_synthetic_unit_fixture(self):
        # Temporary synthetic data checks the fitter math only; never research evidence.
        from research.calibration import COLUMNS,COEFFICIENTS
        rng=np.random.default_rng(42);coef=np.array([.7,.015,.08,.2])
        with tempfile.TemporaryDirectory() as d:
            write_template(d);p=Path(d);rows=[]
            for split,n in [('calibration',12),('validation',6)]:
                for j in range(n):
                    distance,seconds,turn=rng.uniform([1,4,0],[30,100,5]);target=np.array([distance,seconds,turn,1.])@coef
                    rows.append(dict(mission_id=f'{split}_{j%3}',map_id=f'{split}_map_{j%3}',split=split,distance_m=distance,seconds=seconds,turn_radians=turn,electrical_energy_wh=target*.5))
            def write_rows():
                with (p/'electrical_measurements.csv').open('w',newline='') as f:
                    w=csv.DictWriter(f,fieldnames=COLUMNS);w.writeheader();w.writerows(rows)
            write_rows();metadata=dict(measurement_origin='external_hardware',usable_battery_capacity_wh=50,sensor_description='SYNTHETIC UNIT TEST ONLY; not hardware evidence')
            (p/'metadata.json').write_text(json.dumps(metadata))
            result=fit(p/'electrical_measurements.csv',p/'metadata.json')
            np.testing.assert_allclose([result['coefficients'][k] for k in COEFFICIENTS],coef,atol=1e-10)
            self.assertLess(result['validation_rmse_pp'],1e-10)
            rows[-1]['map_id']=rows[0]['map_id'];write_rows()
            with self.assertRaisesRegex(ValueError,'disjoint'):fit(p/'electrical_measurements.csv',p/'metadata.json')
    def test_calibration_rejects_simulated_ledger(self):
        with tempfile.TemporaryDirectory() as d:
            write_template(d);p=Path(d);metadata=json.loads((p/'metadata.json').read_text());metadata['measurement_origin']='simulator'
            (p/'metadata.json').write_text(json.dumps(metadata))
            with self.assertRaisesRegex(ValueError,'external electrical'):fit(p/'electrical_measurements.csv',p/'metadata.json')
        with self.assertRaises(ValueError):validate_profile({'status':'synthetic_test_only'})

if __name__=='__main__':unittest.main()
