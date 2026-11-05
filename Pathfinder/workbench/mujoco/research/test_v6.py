"""Tracking safety, real OMPL adapters, score fairness and electrical units."""
import copy,json,math,tempfile,time,unittest
from pathlib import Path
import numpy as np
from research import tracking,external_planners,swarm
from research.final_study import objective
from research.planning import Limits,plan
import research.test_research as fixtures
from research.electrical_logging import integrate

class V6Tests(unittest.TestCase):
    def graph(self):
        g=fixtures.ResearchTests().graph();g.nav.clear=lambda p,margin=0:g.nav.segment_clear(p,p,margin=margin);return g
    def test_corner_cannot_be_skipped_when_next_connector_is_unsafe(self):
        g=self.graph()
        def clear(a,b,margin=0):
            a,b=np.asarray(a),np.asarray(b);v=b-a;c=np.array([2.4,1.4]);t=np.clip((c-a)@v/max(v@v,1e-12),0,1)
            return np.linalg.norm(a+t*v-c)>.55
        g.nav.segment_clear=clear;f=tracking.SafeFollower(g.nav);points=[np.array([1.,1.]),np.array([3.,1.]),np.array([3.,3.])]
        self.assertFalse(f.may_advance(np.array([2.91,1.]),points,1));self.assertTrue(f.may_advance(np.array([3.,1.]),points,1))
    def test_alignment_hysteresis_stops_translation_until_aligned(self):
        f=tracking.SafeFollower(self.graph().nav)
        self.assertFalse(f.translation_allowed(1.));self.assertFalse(f.translation_allowed(.12));self.assertTrue(f.translation_allowed(.03))
    def test_unrecoverable_guard_fails_closed(self):
        f=tracking.SafeFollower(self.graph().nav);f.nav.segment_clear=lambda *a,**kw:False;points=[np.array([1.,1.]),np.array([5.,5.])]
        result=None
        for i in range(400):
            result=f.observe_guard(np.array([2.,2.]),points,1,True,.016,i*.016)
            if result:break
        self.assertEqual(result,'tracking_guard');self.assertEqual(f.recoveries,0)
    def test_native_ompl_methods_return_common_safe_metrics(self):
        for method in external_planners.METHODS:
            g=self.graph();r=plan(g,np.array([1.,1.]),np.array([6.,6.]),method,Limits(100,100,100,.6),0.,seed=482)
            self.assertTrue(r['admissible']);self.assertEqual(r['optimizer']['library'],'OMPL');self.assertEqual(r['optimizer']['worker_exitcode'],0)
            np.testing.assert_allclose(r['points'][0],[1,1]);np.testing.assert_allclose(r['points'][-1],[6,6]);self.assertAlmostEqual(r['quality_score'],swarm.quality(g.metrics(r['points'])))
    def test_native_ompl_never_promotes_an_approximate_disconnected_path(self):
        for method in ['ompl_rrtstar','ompl_rrtconnect']:
            g=self.graph();g.nav.clear=lambda p,margin=0:abs(p[0]-4)>.55
            g.nav.segment_clear=lambda a,b,margin=0:not(min(a[0],b[0])<=4.55 and max(a[0],b[0])>=3.45)
            r=plan(g,np.array([1.,1.]),np.array([6.,6.]),method,Limits(100,100,100,.3),0.,seed=482)
            self.assertFalse(r['admissible']);self.assertFalse(r['optimizer']['native_exact_solution'])
    def test_weight_changes_apply_to_ranking_and_restore_on_error(self):
        m=dict(distance_m=20.,estimated_seconds=30.,energy_percent=10.,terrain_exposure=8.)
        baseline=swarm.quality(m);before=swarm.QUALITY_WEIGHTS.copy()
        with objective('distance'):self.assertAlmostEqual(swarm.quality(m)-baseline,20/50)
        with self.assertRaises(RuntimeError):
            with objective('terrain'):raise RuntimeError('test')
        np.testing.assert_array_equal(swarm.QUALITY_WEIGHTS,before)
    def test_voltage_current_integration_uses_wh_and_rejects_simulator_origin(self):
        with tempfile.TemporaryDirectory() as temp:
            d=Path(temp);samples=d/'samples.csv';meta=d/'metadata.json';samples.write_text('timestamp_s,voltage_v,discharge_current_a\n0,12,2\n1800,12,2\n3600,12,2\n')
            m=dict(measurement_origin='external_hardware',sensor_description='unit-test fixture only',mission_id='fixture',map_id='fixture',split='calibration',distance_m=1.,turn_radians=0.)
            meta.write_text(json.dumps(m));self.assertAlmostEqual(integrate(samples,meta)['electrical_energy_wh'],24.)
            m['measurement_origin']='simulation';meta.write_text(json.dumps(m))
            with self.assertRaises(ValueError):integrate(samples,meta)

if __name__=='__main__':unittest.main()
