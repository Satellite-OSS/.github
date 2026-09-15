import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('badges', Path(__file__).with_name('traffic-badges.py'))
badges = importlib.util.module_from_spec(spec)
spec.loader.exec_module(badges)


class BadgeTests(unittest.TestCase):
    def test_sum_refresh_and_unchanged_rerun(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, count in [('a', 12), ('b', 34)]:
                folder = root / name
                folder.mkdir()
                (folder / 'views_clones_aggregate.csv').write_text(
                    f'time_iso8601,views_total\n2026-09-14,10\n2026-09-15,{count - 10}\n')
                (folder / 'views.svg').write_text(f'<svg aria-label="views: {count}"/>')
            (root / 'a' / 'views.svg').write_text('<svg aria-label="views: 10"/>')
            with patch.object(badges, 'urlopen', return_value=io.BytesIO(b'<svg aria-label="views: 12"/>')) as request:
                badges.generate(root)
                request.assert_called_once()
            self.assertEqual(json.loads((root / 'repo-views.json').read_text())['message'], '46')
            before = {p: p.read_bytes() for p in root.rglob('*') if p.is_file()}
            with patch.object(badges, 'urlopen', side_effect=AssertionError('Unchanged badge fetched')):
                badges.generate(root)
            self.assertEqual(before, {p: p.read_bytes() for p in root.rglob('*') if p.is_file()})


if __name__ == '__main__':
    unittest.main()
