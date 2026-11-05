"""Correctness checks for free waypoint refinement and incumbent preservation."""
import math,time,unittest
from unittest.mock import patch
import numpy as np
from research import advanced
import research.test_research as fixtures
from research.planning import Limits,plan

class AdvancedTests(unittest.TestCase):
    def test_polishing_improves_safe_detour_without_changing_endpoints(self):
        g=fixtures.ResearchTests().graph()
        def clear(a,b,margin=0):
            a,b=np.asarray(a),np.asarray(b);d=b-a;t=np.clip((np.array([4.,1.])-a)@d/max(d@d,1e-12),0,1)
            return np.linalg.norm(a+t*d-np.array([4.,1.]))>.7
        g.nav.segment_clear=clear;route=[np.array(p,float) for p in [(1,1),(3,6),(7,1)]];begin=time.perf_counter()
        pool=advanced.Candidates(g,Limits(100,100,100,2),2.,0.,begin,begin+2);pool.evaluate(route);before=pool.best[0]
        advanced.polish(pool);self.assertLess(pool.best[0],before);self.assertGreater(pool.accepted_moves,0)
        np.testing.assert_allclose(pool.best[1][0],route[0]);np.testing.assert_allclose(pool.best[1][-1],route[-1])
        self.assertTrue(all(clear(a,b) for a,b in zip(pool.best[1],pool.best[1][1:])))
        self.assertLessEqual(pool.evaluations,240)
    def test_known_incumbent_survives_exhausted_cap_and_expired_clock(self):
        g=fixtures.ResearchTests().graph();route=[np.array([1.,1.]),np.array([6.,6.])];now=time.perf_counter();m=g.metrics(route)
        pool=advanced.Candidates(g,Limits(),0.,math.pi/2,now-3,now-1,used=240)
        self.assertIsNotNone(pool.evaluate(route,known_metrics=m));self.assertIsNotNone(pool.best);self.assertFalse(pool.live())
    def test_infeasible_route_remains_rejected(self):
        g=fixtures.ResearchTests().graph()
        for method in ['proposed_v4','pso_polished','aco_polished']:
            result=plan(g,np.array([1.,1.]),np.array([6.,6.]),method,Limits(60,4,100,.5),2.)
            self.assertFalse(result['admissible']);self.assertLessEqual(result['optimizer']['fitness_evaluations'],240)
    def test_composite_quality_and_ablation_flags(self):
        g=fixtures.ResearchTests().graph()
        for method,flag in [('proposed_v4_no_polish','continuous_polish'),('proposed_v4_no_landmarks','landmark_diversification')]:
            r=plan(g,np.array([1.,1.]),np.array([6.,6.]),method,Limits(60,100,100,1.),2.)
            self.assertTrue(r['admissible']);self.assertFalse(r['optimizer']['parameters'][flag])
            self.assertAlmostEqual(r['quality_score'],advanced.quality(r['metrics']))
    def test_no_landmarks_control_matches_polishing_operator(self):
        g=fixtures.ResearchTests().graph();now=time.perf_counter();pool=advanced.Candidates(g,Limits(),0.,0.,now,now+1)
        nodes=advanced.landmarks(pool,np.array([1.,1.]),np.array([6.,6.]),[],8)
        np.testing.assert_allclose(nodes[:2],[[1,1],[6,6]])
        self.assertLessEqual(len(nodes),8)

if __name__=='__main__':unittest.main()
