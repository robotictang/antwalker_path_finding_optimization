"""Regression for the end-to-end planning result persistence failure."""
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from research.run import atomic_json


class PersistenceTests(unittest.TestCase):
    def test_numpy_route_and_scalar_values_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'result.json'
            atomic_json(path, dict(points=[np.array([1., 2.], dtype=np.float32)],
                                   score=np.float32(.5), count=np.int64(2),
                                   admitted=np.bool_(True)))
            self.assertEqual(json.loads(path.read_text()),
                             dict(points=[[1., 2.]], score=.5, count=2, admitted=True))

    def test_nonfinite_numpy_value_cannot_replace_saved_record(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'result.json'
            atomic_json(path, dict(state='complete'))
            with self.assertRaises(ValueError):
                atomic_json(path, dict(score=np.float32('nan')))
            self.assertEqual(json.loads(path.read_text()), dict(state='complete'))


if __name__ == '__main__':
    unittest.main()
