"""Render README badges from github-repo-stats' daily aggregate CSVs."""
import csv
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen
from xml.etree import ElementTree


def generate(root):
    total = 0
    for aggregate in sorted(root.glob('*/views_clones_aggregate.csv')):
        with aggregate.open(newline='') as stream:
            count = sum(int(row['views_total']) for row in csv.DictReader(stream))
        total += count
        output = aggregate.parent / 'views.svg'
        if output.exists() and ElementTree.parse(output).getroot().attrib.get('aria-label') == f'views: {count}':
            continue
        query = urlencode({'label': 'views', 'message': str(count),
                           'color': 'brightgreen', 'logo': 'github'})
        with urlopen('https://img.shields.io/static/v1?' + query, timeout=30) as response:
            svg = response.read()
        label = ElementTree.fromstring(svg).attrib.get('aria-label')
        if label != f'views: {count}':
            raise ValueError(f'Unexpected badge for {aggregate}: {label}')
        output.write_bytes(svg)
    badge = {'schemaVersion': 1, 'label': 'Repo views',
             'message': str(total), 'color': 'brightgreen'}
    (root / 'repo-views.json').write_text(json.dumps(badge, indent=2) + '\n')


if __name__ == '__main__':
    generate(Path('traffic'))
