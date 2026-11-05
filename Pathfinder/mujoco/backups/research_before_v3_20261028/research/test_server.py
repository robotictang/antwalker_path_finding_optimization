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
    def test_snapshot_is_sent_as_exact_json_bytes(self):
        with urlopen(self.base+'/comparison/snapshot.test.json') as r:
            self.assertEqual(r.status,200)
            self.assertEqual(r.headers['Content-Type'],'application/json')
            self.assertEqual(int(r.headers['Content-Length']),len(self.raw))
            self.assertEqual(r.read(),self.raw)
    def test_api_objects_still_serialize_once(self):
        with urlopen(self.base+'/api/result?run=saved_test') as r:self.assertEqual(json.load(r),self.record)
    def test_html_and_download_still_work(self):
        with urlopen(self.base+'/comparison/') as r:self.assertIn(b'Comparison',r.read())
        with urlopen(self.base+'/api/download?run=saved_test&format=json') as r:self.assertEqual(json.load(r),self.record)

if __name__=='__main__':unittest.main()
