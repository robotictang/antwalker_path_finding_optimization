"""Checks for paired denominators, parameter isolation and physical map variation."""
import copy
import unittest
import mujoco
import numpy as np
from research.reliability import parameters,selection_key,paired_report
from research.swarm import PARAMETERS
from research.run import model_for_case
from safe_navigation import SafeNavigator

class ReliabilityTests(unittest.TestCase):
    def test_parameters_restore_after_failure(self):
        original=copy.deepcopy(PARAMETERS);changed=copy.deepcopy(original);changed['pso']['particles']=23
        with self.assertRaises(RuntimeError):
            with parameters(changed):
                self.assertEqual(PARAMETERS['pso']['particles'],23)
                raise RuntimeError('cancel')
        self.assertEqual(PARAMETERS,original)

    def test_selection_prioritizes_admission(self):
        def result(scores):return {'records':[dict(method='pso',plan=dict(admissible=s is not None,quality_score=s)) for s in scores]}
        self.assertLess(selection_key(result([8.,9.]),'pso'),selection_key(result([.1,None]),'pso'))

    def test_paired_counts_keep_rejections_and_cluster_seeds(self):
        records=[]
        scores={'a':{'proposed':[1.,1.],'pso':[2.,2.],'aco':[1.,1.]},
                'b':{'proposed':[None,None],'pso':[3.,None],'aco':[None,None]}}
        for case,methods in scores.items():
            for method,values in methods.items():
                for repeat,score in enumerate(values):records.append(dict(case_id=case,method=method,repeat=repeat,plan=dict(admissible=score is not None,quality_score=score)))
        report=paired_report(dict(run_id='test',records=records,cases=[dict(id='a'),dict(id='b')],repeats=2,summary=[]))
        pso,aco=report['comparisons']
        self.assertEqual((pso['wins'],pso['ties'],pso['baseline_only_admitted'],pso['both_rejected']),(2,0,1,1))
        self.assertEqual(pso['layouts_with_paired_admission'],1)
        self.assertIsNone(pso['descriptive_layout_bootstrap_95_percent'])
        self.assertEqual((aco['ties'],aco['both_rejected']),(2,2))

    def test_hazard_changes_physics_and_navigation_together(self):
        boxes=[]
        for position in [[-2.,-26.,0.],[25.,-21.,0.]]:
            model=model_for_case(hazard_position=position);data=mujoco.MjData(model);mujoco.mj_forward(model,data)
            geom=model.geom('roadwork_collision').id
            np.testing.assert_allclose(data.geom_xpos[geom,:2],position[:2])
            nav=SafeNavigator(model,data,resolution=.25)
            self.assertIn(geom,nav.obstacle_geoms)
            boxes.append(nav.boxes)
        self.assertFalse(np.array_equal(*boxes))

if __name__=='__main__':unittest.main()
