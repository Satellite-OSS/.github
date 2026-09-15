"""Sum github-repo-stats CSVs by date and render the README badges."""
import csv
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree


def render(output, label, count):
    expected = f'{label}: {count}'
    if output.exists() and ElementTree.parse(output).getroot().attrib.get('aria-label') == expected:
        return
    query = urlencode({'label': label, 'message': str(count), 'color': 'brightgreen',
                       'logo': 'github', 'style': 'flat-square'})
    request = Request('https://img.shields.io/static/v1?' + query, headers={'User-Agent': 'Satellite-OSS-traffic'})
    with urlopen(request, timeout=30) as response:
        svg = response.read()
    if ElementTree.fromstring(svg).attrib.get('aria-label') != expected:
        raise ValueError(f'Unexpected badge for {output}')
    output.write_bytes(svg)


def generate(root):
    daily = defaultdict(lambda: {'clones_total': 0, 'views_total': 0})
    for aggregate in sorted(root.glob('*.csv')):
        if aggregate.name == 'sum.csv':
            continue
        with aggregate.open(newline='') as stream:
            rows = list(csv.DictReader(stream))
        for row in rows:
            for metric in ('clones_total', 'views_total'):
                daily[row['time_iso8601']][metric] += int(row[metric])
        render(aggregate.with_suffix('.svg'), 'views', sum(int(r['views_total']) for r in rows))
    with (root / 'sum.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=['time_iso8601', 'clones_total', 'views_total'], lineterminator='\n')
        writer.writeheader()
        writer.writerows({'time_iso8601': day, **daily[day]} for day in sorted(daily))
    render(root / 'sum.svg', 'Repo views', sum(row['views_total'] for row in daily.values()))


if __name__ == '__main__':
    generate(Path('traffic'))
