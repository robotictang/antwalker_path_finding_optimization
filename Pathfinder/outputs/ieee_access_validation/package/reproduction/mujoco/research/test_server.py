"""HTTP regressions for chart snapshots and saved-result delivery."""
import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.request import urlopen
from unittest.mock import patch
from http.server import ThreadingHTTPServer
from research import server

class ServerDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();root=Path(self.temp.name)
        self.dist=root/'research_dashboard/dist';self.dist.mkdir(parents=True)
        out=root/'outputs/research';out.mkdir(parents=True)
        self.record={'run_id':'saved_test','records':[{'case_id':'test','status':'found'}]}
        (out/'saved_test.json').write_text(json.dumps(self.record))
        self.raw=b'{"queries":{"trials":{"rows":[{"case":"test"}]}}}'
        (self.dist/'snapshot.test.json').write_bytes(self.raw)
        (self.dist/'index.html').write_text('<!doctype html><title>Comparison</title>')
        self.patches=[patch.object(server,'ROOT',root),patch.object(server,'OUT',out)]
        for p in self.patches:p.start()
        self.http=ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        self.thread=threading.Thread(target=self.http.serve_forever,daemon=True);self.thread.start()
        self.base=f'http://127.0.0.1:{self.http.server_port}'
    def tearDown(self):
        self.http.shutdown();self.http.server_close();self.thread.join()
        for p in reversed(self.patches):p.stop()
        self.temp.cleanup()
    def test_study_endpoint_prefers_v3_and_preserves_v1_fallback(self):
        old=server.OUT/'reliability_v1/study_summary.json';old.parent.mkdir();old.write_text('{"version":1}')
        with urlopen(self.base+'/api/study') as r:self.assertEqual(json.load(r)['version'],1)
        new=server.OUT/'strong_study_v3/study_summary.json';new.parent.mkdir();new.write_text('{"version":3}')
        with urlopen(self.base+'/api/study') as r:self.assertEqual(json.load(r)['version'],3)
        v4=server.OUT/'advanced_study_v4/study_summary.json';v4.parent.mkdir();v4.write_text('{"version":4}')
        with urlopen(self.base+'/api/study') as r:self.assertEqual(json.load(r)['version'],4)
        with urlopen(self.base+'/api/study?version=3') as r:self.assertEqual(json.load(r)['version'],3)
    def test_procedural_seed_validation_rejects_bad_inputs(self):
        for seed in [True,0,-1,2000000001,1.25,'123']:
            with self.assertRaisesRegex(ValueError,'World seed'):server.launch(dict(kind='benchmark',suite='procedural4',world_seed=seed))
    def test_new_world_suite_and_seed_reach_cli(self):
        with patch.object(server.subprocess,'Popen',side_effect=RuntimeError('captured without launching')) as spawn:
            with self.assertRaisesRegex(RuntimeError,'captured'):server.launch(dict(kind='benchmark',suite='procedural12',world_seed=1070000,execute=False))
            command=spawn.call_args.args[0]
        self.assertEqual(command[command.index('--suite')+1],'procedural12')
        self.assertEqual(command[command.index('--world-seed')+1],'1070000')
    def test_v4_hybrid_mode_is_rejected_before_job_launch(self):
        with self.assertRaisesRegex(ValueError,'walking only'):
            server.launch(dict(kind='benchmark',suite='procedural4',methods=['proposed_v4'],hybrid=True))
    def test_snapshot_is_sent_as_exact_json_bytes(self):
        with urlopen(self.base+'/comparison/snapshot.test.json') as r:
            self.assertEqual(r.status,200)
            self.assertEqual(r.headers['Content-Type'],'application/json')
            self.assertEqual(int(r.headers['Content-Length']),len(self.raw))
            self.assertEqual(r.read(),self.raw)
    def test_v5_hybrid_is_rejected_before_process_launch(self):
        with patch.object(server.subprocess,'Popen') as spawn:
            with self.assertRaisesRegex(ValueError,'walking only'):server.launch(dict(kind='benchmark',methods=['proposed_v5'],hybrid=True))
            spawn.assert_not_called()
    def test_v5_default_view_preserves_explicit_v4_access(self):
        fresh=server.OUT/'validation_extension_v5/study_summary.json';fresh.parent.mkdir();fresh.write_text('{"version":5,"phase_counts":{}}')
        old=server.OUT/'advanced_study_v4/study_summary.json';old.parent.mkdir();old.write_text('{"version":4}')
        with urlopen(self.base+'/api/study') as r:self.assertEqual(json.load(r)['version'],5)
        with urlopen(self.base+'/api/study?version=4') as r:self.assertEqual(json.load(r)['version'],4)
    def test_load_preserved_study_only_exports_saved_records(self):
        old=server.OUT/'advanced_study_v4/study_summary.json';old.parent.mkdir();old.write_text('{"planning_report":{"run_id":"saved_test"}}')
        with patch.object(server.subprocess,'Popen',side_effect=RuntimeError('captured')) as spawn:
            with self.assertRaisesRegex(RuntimeError,'captured'):server.launch(dict(kind='advanced-study'))
        command=spawn.call_args.args[0]
        self.assertIn('research.export_dashboard',command);self.assertNotIn('research.advanced_study',command)
    def test_api_objects_still_serialize_once(self):
        with urlopen(self.base+'/api/result?run=saved_test') as r:self.assertEqual(json.load(r),self.record)
    def test_html_and_download_still_work(self):
        with urlopen(self.base+'/comparison/') as r:self.assertIn(b'Comparison',r.read())
        with urlopen(self.base+'/api/download?run=saved_test&format=json') as r:self.assertEqual(json.load(r),self.record)

if __name__=='__main__':unittest.main()
