"""Small independent correctness checks for research safety and measurements."""
import math
import time
import unittest
import numpy as np
from research.planning import SceneGraph,Limits,plan,scalar_search,feasible
from energy_model import energy_cost
from tripod_gait import TripodGait
from research.telemetry import Telemetry
from research.swarm import Corridor,particle_swarm,ant_colony,pareto_beam,resource_label_search
from types import SimpleNamespace

class ToyNav:
    n=9;lower=0.;upper=8.;resolution=1.;radius=.05;tracking_margin=0.
    force_mode=None;current_mode='legs';hybrid=True;walk_speed=.75;wheel_speed=1.65
    def __init__(self):self.blocked=np.zeros((9,9),bool);self.boxes=np.empty((0,2,2))
    def point(self,c):return np.asarray(c,dtype=float)
    def nearest_free(self,p):return tuple(np.rint(p).astype(int))
    def segment_clear(self,a,b,margin=0):return True
    def route_metrics(self,points,yaw):
        delta=np.diff(points,axis=0);length=np.linalg.norm(delta,axis=1).sum()
        angles=np.arctan2(delta[:,1],delta[:,0]);turn=np.abs((np.diff(np.r_[yaw,angles])+math.pi)%(2*math.pi)-math.pi).sum()
        seconds=length/.75+turn+.6
        return dict(distance_m=float(length),estimated_seconds=float(seconds),energy_percent=energy_cost(0,length,seconds,turn,0),walking_distance_m=float(length),driving_distance_m=0.,transformations=0)

class ResearchTests(unittest.TestCase):
    def graph(self):
        graph=SceneGraph(ToyNav())
        # Independent controlled edges: no terrain costs, constant speed.
        for node in range(81):
            for k,nxt in enumerate(graph.neighbors[node]):
                if nxt>=0:
                    length=np.linalg.norm(graph.point(node)-graph.point(nxt))
                    graph.edges[node,k]=[length,length/.75,length*.72,0.]
        graph.difficulty[:]=0.;graph._bounds={}
        return graph
    def test_astar_matches_uninformed_reference(self):
        g=self.graph();a=np.array([1.,1.]);b=np.array([7.,6.])
        route,_,status=scalar_search(g,a,b,[1.,0,0,0],0,time.perf_counter()+2,10000)
        self.assertEqual(status,'found')
        expected=5*math.sqrt(2)+1
        self.assertAlmostEqual(sum(np.linalg.norm(y-x) for x,y in zip(route,route[1:])),expected)
    def test_constrained_search_and_infeasible_battery(self):
        g=self.graph();a=np.array([1.,1.]);b=np.array([6.,6.])
        result=plan(g,a,b,'proposed_v1',Limits(60,100,100,2),2.)
        self.assertTrue(result['admissible']);self.assertGreater(len(result['points']),1)
        impossible=plan(g,a,b,'proposed_v1',Limits(60,4,100,2),2.)
        self.assertFalse(impossible['admissible']);self.assertIsNone(impossible['metrics'])
    def test_battery_includes_return(self):
        m=dict(estimated_seconds=10,energy_percent=20,terrain_exposure=1)
        c=feasible(m,Limits(20,50,2),20)
        self.assertFalse(c['battery_ok']);self.assertEqual(c['required_battery_percent'],56)
    def test_default_gait_preserved_and_parameters_validated(self):
        g=TripodGait();self.assertAlmostEqual(g.period,1/1.45);self.assertEqual(g.duty,.6)
        with self.assertRaises(ValueError):TripodGait(duty=.2)
        for period in (.6,.8,1.):
            g=TripodGait(period=period,duty=.65)
            for _ in range(10):self.assertTrue(np.isfinite(g.targets(np.array([-30.,-15.]),0.,1.2,.3,0.)).all())
    def test_work_integral_and_self_contact_exclusion(self):
        model=SimpleNamespace(body=lambda name:SimpleNamespace(id=1),nbody=3,ngeom=3,
          body_parentid=np.array([0,0,1]),geom_bodyid=np.array([0,2,1]))
        telemetry=Telemetry(model,[1],[0])
        data=SimpleNamespace(actuator_force=np.array([2.,-3.]),actuator_velocity=np.array([4.,2.]),
          xquat=np.array([[1.,0,0,0]]*3),contact=[SimpleNamespace(dist=0.,geom1=1,geom2=2)])
        telemetry.sample(data,.1)
        self.assertAlmostEqual(telemetry.work,.8);self.assertAlmostEqual(telemetry.abs_work,1.4)
        self.assertEqual(telemetry.support_sum,0)
    def test_swarm_refiners_are_reproducible_and_keep_endpoints(self):
        g=self.graph();a=np.array([1.,1.]);b=np.array([6.,6.]);limits=Limits(60,100,100,2)
        for method in ('pso','aco','b7_greedy','proposed','proposed_v1'):
            r=plan(g,a,b,method,limits,2.,seed=41)
            self.assertTrue(r['admissible'],(method,r))
            np.testing.assert_allclose(r['points'][0],a);np.testing.assert_allclose(r['points'][-1],b)
            if method in ('pso','aco'):
                repeat=plan(g,a,b,method,limits,2.,seed=41)
                np.testing.assert_allclose(r['points'],repeat['points'])
                self.assertIn('fitness_evaluations',r['optimizer'])
                self.assertEqual(len(r['optimizer']['seed_status']),3)
    def test_swarm_does_not_bypass_resource_constraints(self):
        g=self.graph()
        for method in ('pso','aco','proposed'):
            r=plan(g,np.array([1.,1.]),np.array([6.,6.]),method,Limits(60,4,100,1),2.,seed=2)
            self.assertFalse(r['admissible'])
    def test_optimizers_improve_a_nontrivial_obstacle_corridor(self):
        g=self.graph()
        points=[np.array(p,float) for p in [(0,0),(1,3),(2,1),(3,3),(4,0)]]
        def clear(a,b,margin=0):
            a,b=np.asarray(a),np.asarray(b);delta=b-a
            t=np.clip(np.dot(np.array([2.,0.])-a,delta)/max(1e-12,delta@delta),0,1)
            return np.linalg.norm(a+t*delta-np.array([2.,0.]))>.5
        g.nav.segment_clear=clear
        for algorithm in (particle_swarm,ant_colony,pareto_beam,resource_label_search):
            begin=time.perf_counter();c=Corridor(g,points,0.,Limits(100,100,100,3),0.,begin+3,begin);c.initialize()
            before=c.best[0][2]
            if algorithm in (pareto_beam,resource_label_search):details=algorithm(c)
            else:details=algorithm(c,np.random.default_rng(19))
            self.assertLess(c.best[0][2],before)
            self.assertGreater(details['iterations'],0)
            route=c.result();self.assertTrue(all(clear(a,b) for a,b in zip(route,route[1:])))
            self.assertAlmostEqual(sum(np.linalg.norm(b-a) for a,b in zip(route,route[1:])),2*math.sqrt(5))

if __name__=='__main__':unittest.main()
