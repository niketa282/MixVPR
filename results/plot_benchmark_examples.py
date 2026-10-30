"""Poster grid: one query image from each of the 15 test sets, grouped by condition.

By default the middle query of each set is shown; override with --pick name=index (e.g. --pick tokyo247=120).
Output: results/figures/poster/benchmark_examples.png

Usage:
    python results/plot_benchmark_examples.py [--pick msls_val=500 ...]
"""
import argparse
import glob
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEOSETS = '/iridisfs/geosets'
QUERIES = {  # same query folders as eval.py TEST_SETS
    'pitts30k_test': 'pitts30k/images/test/queries', 'pitts250k_test': 'pitts250k/images/test/queries',
    'msls_val': 'msls/val/queries', 'sf_xl_small': 'small/test/queries_v1',
    'tokyo247': 'tokyo247/images/test/queries', 'amstertime': 'amstertime/images/test/queries',
    'st_lucia': 'st_lucia/images/test/queries', 'eynsham': 'eynsham/images/test/queries',
    'nordland': 'nordland/images/test/queries', 'svox_overcast': 'svox/images/test/queries_overcast',
    'svox_rain': 'svox/images/test/queries_rain', 'svox_snow': 'svox/images/test/queries_snow',
    'svox_sun': 'svox/images/test/queries_sun', 'svox': 'svox/images/test/queries',
    'svox_night': 'svox/images/test/queries_night'}
NAMES = {'pitts30k_test': 'Pitts30k', 'pitts250k_test': 'Pitts250k', 'msls_val': 'MSLS', 'sf_xl_small': 'SF-XL',
         'tokyo247': 'Tokyo 24/7', 'amstertime': 'AmsterTime', 'st_lucia': 'St Lucia', 'eynsham': 'Eynsham',
         'nordland': 'Nordland (winter)', 'svox_overcast': 'SVOX Overcast', 'svox_rain': 'SVOX Rain',
         'svox_snow': 'SVOX Snow', 'svox_sun': 'SVOX Sun', 'svox': 'SVOX (all)', 'svox_night': 'SVOX Night'}
GROUPS = [('General benchmarks', '#2a78d6',
           ['pitts30k_test', 'pitts250k_test', 'msls_val', 'sf_xl_small', 'tokyo247', 'amstertime', 'st_lucia',
            'eynsham']),
          ('Seasonal & weather', '#1baf7a',
           ['nordland', 'svox_overcast', 'svox_rain', 'svox_snow', 'svox_sun', 'svox']),
          ('Night', '#c98500', ['svox_night'])]
TEXT = '#1f1f1e'
FS = 18


def square(img, size=512):
    w, h = img.size
    s = min(w, h)
    return img.crop(((w - s) // 2, (h - s) // 2, (w + s) // 2, (h + s) // 2)).resize((size, size))


def query_paths(name):
    d = os.path.join(GEOSETS, QUERIES[name])
    paths = sorted(glob.glob(os.path.join(d, '*.jpg'))) or sorted(glob.glob(os.path.join(d, '**', '*.jpg'),
                                                                              recursive=True))
    if not paths:
        raise FileNotFoundError(d)
    return paths


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pick', nargs='*', default=[], help='name=index overrides')
    args = ap.parse_args()
    pick = {k: int(v) for k, v in (p.split('=') for p in args.pick)}

    order = [(name, col, g) for g, col, names in GROUPS for name in names]  # 15 panels
    ncol = 5
    fig, axes = plt.subplots(3, ncol, figsize=(16, 11.2))
    for ax, (name, col, group) in zip(axes.flat, order):
        paths = query_paths(name)
        i = pick.get(name, len(paths) // 2)
        ax.imshow(square(Image.open(paths[i]).convert('RGB')))
        ax.set_xticks([]); ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_edgecolor(col); sp.set_linewidth(5)
        ax.set_title(NAMES[name], fontsize=FS, color=TEXT, pad=8)
        print(f'{name:15s} {i:6d} / {len(paths)}  {os.path.basename(paths[i])}')
    handles = [plt.Rectangle((0, 0), 1, 1, facecolor='white', edgecolor=c, linewidth=4, label=g) for g, c, _ in GROUPS]
    fig.legend(handles=handles, loc='lower center', ncol=3, frameon=False, fontsize=FS, bbox_to_anchor=(0.5, -0.03),
               handlelength=1.4, handleheight=1.0)
    fig.tight_layout(rect=(0, 0.03, 1, 1), h_pad=1.2, w_pad=0.8)
    os.makedirs('results/figures/poster', exist_ok=True)
    out = 'results/figures/poster/benchmark_examples.png'
    fig.savefig(out, dpi=250, bbox_inches='tight', pad_inches=0.1, facecolor='white')
    print('saved', out)


if __name__ == '__main__':
    main()
