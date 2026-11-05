"""Safety, resource ordering and experiment isolation for the V5 extension."""
import copy,math,time,unittest
from types import SimpleNamespace
import numpy as np
from research import adaptive,advanced,swarm
from research.extension_study import configuration,profiles
from research.planning import Limits,plan
import research.test_research as fixtures

class V5Tests(unittest.TestCase):
    def test_all_variants_preserve_endpoints_and_collision_safety(self):
        for method in ['proposed_v5','proposed_v5_fixed','proposed_v5_no_polish','proposed_v5_no_landmarks']:
            g=fixtures.ResearchTests().graph();start=np.array([1.,1.]);goal=np.array([6.,6.])
            r=plan(g,start,goal,method,Limits(100,100,100,.5),2.)
            self.assertTrue(r['admissible']);np.testing.assert_allclose(r['points'][0],start);np.testing.assert_allclose(r['points'][-1],goal)
            self.assertTrue(all(g.nav.segment_clear(a,b,margin=g.nav.tracking_margin) for a,b in zip(r['points'],r['points'][1:])))
            self.assertAlmostEqual(r['quality_score'],swarm.quality(r['metrics']))
    def test_rejected_route_cannot_become_fake_success(self):
        g=fixtures.ResearchTests().graph();r=plan(g,np.array([1.,1.]),np.array([6.,6.]),'proposed_v5',Limits(100,4,100,.5),2.)
        self.assertFalse(r['admissible']);self.assertFalse(r['battery_ok'])
    def test_resource_priority_does_not_change_objective(self):
        metrics=dict(distance_m=10.,estimated_seconds=20.,energy_percent=10.,terrain_exposure=50.)
        pool=SimpleNamespace(best=((1,1.,2.),[],metrics),limits=Limits(100,100,10,1),return_energy=2.)
        weights,ratios=adaptive.search_weights(pool,True)
        np.testing.assert_allclose(weights[0],[0,0,0,1]);self.assertEqual(max(ratios),5.)
        np.testing.assert_allclose(adaptive.search_weights(pool,False)[0][0],[1/50,1/90,1/30,.25/20])
    def test_candidate_ceiling_covers_seed_plus_refinement(self):
        cfg=profiles()['default']
        for method in ['proposed_v4','pso_polished','aco_polished','proposed_v5']:
            with configuration(cfg,80):
                g=fixtures.ResearchTests().graph();r=plan(g,np.array([1.,1.]),np.array([6.,6.]),method,Limits(100,100,100,.5),2.)
                self.assertLessEqual(r['optimizer']['fitness_evaluations'],80)
    def test_configuration_restores_after_exception(self):
        before=copy.deepcopy((swarm.PARAMETERS,advanced.PARAMETERS,adaptive.PARAMETERS,swarm.FITNESS_CAP))
        with self.assertRaises(RuntimeError):
            with configuration(profiles()['alternative'],80):raise RuntimeError('test')
        self.assertEqual(before,(swarm.PARAMETERS,advanced.PARAMETERS,adaptive.PARAMETERS,swarm.FITNESS_CAP))
    def test_expired_clock_retains_known_candidate(self):
        g=fixtures.ResearchTests().graph();points=[np.array([1.,1.]),np.array([6.,6.])];now=time.perf_counter()
        pool=advanced.Candidates(g,Limits(),2.,math.pi/2,now-2,now-1,240)
        pool.evaluate(points,known_metrics=g.metrics(points));self.assertIsNotNone(pool.best);self.assertFalse(pool.live())
    def test_bound_does_not_exceed_direct_common_score(self):
        g=fixtures.ResearchTests().graph();a=np.array([1.,1.]);b=np.array([6.,6.])
        self.assertLessEqual(adaptive.optimistic_score(g,a,b),swarm.quality(g.metrics([a,b]))+1e-8)

if __name__=='__main__':unittest.main()
