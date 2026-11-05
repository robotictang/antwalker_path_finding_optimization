"""Correctness checks for the new representation control before test freeze."""
import unittest
import numpy as np
from research.continuous_pso import subdivide
from research.planning import Limits,plan
from research.test_research import ResearchTests


class PublicationTests(unittest.TestCase):
    def test_subdivision_retains_corners_and_endpoints(self):
        original=[np.array([1.,1.]),np.array([1.,4.]),np.array([5.,4.])]
        points=subdivide(original,6)
        self.assertEqual(len(points),8)
        for p in original:self.assertTrue(any(np.array_equal(p,q) for q in points))
        np.testing.assert_array_equal(points[0],original[0]);np.testing.assert_array_equal(points[-1],original[-1])
        self.assertAlmostEqual(sum(np.linalg.norm(b-a) for a,b in zip(points,points[1:])),7.)

    def test_coordinate_pso_uses_common_feasibility_and_safe_endpoints(self):
        g=ResearchTests().graph();a=np.array([1.,1.]);b=np.array([6.,6.])
        r=plan(g,a,b,'continuous_pso',Limits(100,100,100,.6),seed=183)
        self.assertTrue(r['admissible']);np.testing.assert_array_equal(r['points'][0],a);np.testing.assert_array_equal(r['points'][-1],b)
        self.assertTrue(all(g.nav.segment_clear(x,y,margin=g.nav.tracking_margin) for x,y in zip(r['points'],r['points'][1:])))
        self.assertLessEqual(r['optimizer']['fitness_evaluations'],240)

    def test_coordinate_pso_does_not_override_resource_rejection(self):
        g=ResearchTests().graph();r=plan(g,np.array([1.,1.]),np.array([6.,6.]),'continuous_pso',Limits(100,1,100,.4),seed=183)
        self.assertFalse(r['admissible'])


if __name__=='__main__':unittest.main()
