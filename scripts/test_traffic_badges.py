import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('badges', Path(__file__).with_name('traffic-badges.py'))
badges = importlib.util.module_from_spec(spec)
spec.loader.exec_module(badges)


class BadgeTests(unittest.TestCase):
    def test_daily_sum_refresh_and_unchanged_rerun(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, count in [('a', 12), ('b', 34)]:
                (root / f'{name}.csv').write_text(
                    f'time_iso8601,clones_total,views_total\n2026-09-14,1,10\n2026-09-15,2,{count - 10}\n')
                (root / f'{name}.svg').write_text(f'<svg aria-label="views: {count}"/>')
            (root / 'a.svg').write_text('<svg aria-label="views: 10"/>')
            with patch.object(badges, 'urlopen', side_effect=[
                io.BytesIO(b'<svg aria-label="views: 12"/>'),
                io.BytesIO(b'<svg aria-label="Repo views: 46"/>'),
            ]) as request:
                badges.generate(root)
                self.assertEqual(request.call_count, 2)
            self.assertEqual((root / 'sum.csv').read_text(),
                'time_iso8601,clones_total,views_total\n2026-09-14,2,20\n2026-09-15,4,26\n')
            before = {p: p.read_bytes() for p in root.iterdir()}
            with patch.object(badges, 'urlopen', side_effect=AssertionError('Unchanged badge fetched')):
                badges.generate(root)
            self.assertEqual(before, {p: p.read_bytes() for p in root.iterdir()})


if __name__ == '__main__':
    unittest.main()
