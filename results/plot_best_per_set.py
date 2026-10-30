"""Per test set: best geometric vs. best photometric condition (single or mixed), with RandAugment as a marker.

Each bar is labelled with its R@1 gain and the condition that achieved it.

Usage:
    python results/plot_best_per_set.py                 # RGB
    python results/plot_best_per_set.py --suffix _gray  # grayscale
"""
import argparse
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np
import pandas as pd

GEO = ['crop', 'perspective', 'rotate', 'translate', 'shear', 'geo_k1', 'geo_k2', 'geo_k3']
PHO = ['brightness', 'contrast', 'autocontrast', 'blur', 'phot_k1', 'phot_k2', 'phot_k3']
PANELS = [
    ('General benchmarks', [('pitts30k_test', 'Pitts30k'), ('pitts250k_test', 'Pitts250k'), ('msls_val', 'MSLS'),
                            ('sf_xl_small', 'SF-XL'), ('tokyo247', 'Tokyo 24/7'), ('amstertime', 'AmsterTime'),
                            ('st_lucia', 'St Lucia'), ('eynsham', 'Eynsham')]),
    ('Seasonal & weather', [('nordland', 'Nordland'), ('svox', 'SVOX (all)'), ('svox_overcast', 'SVOX Overcast'),
                            ('svox_rain', 'SVOX Rain'), ('svox_snow', 'SVOX Snow'), ('svox_sun', 'SVOX Sun')]),
    ('Night', [('svox_night', 'SVOX Night')]),
]
C_GEO, C_PHO, C_RA = '#2a78d6', '#eb6834', '#c9c8c1'
TEXT, TEXT2, GRID = '#1f1f1e', '#5f5e58', '#e4e3dd'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, nargs='+', default=[190223, 1, 2])
    ap.add_argument('--suffix', default='', help="'' for RGB, '_gray' for grayscale")
    args = ap.parse_args()

    d = pd.concat([pd.read_csv(f'results/seed{s}/test_results{args.suffix}.csv') for s in args.seeds])
    p = d.pivot_table(index=['seed', 'condition'], columns='dataset', values='R1')
    gain = pd.concat([p.loc[s] - p.loc[s].loc['none'] for s in args.seeds], keys=args.seeds)
    gm = gain.groupby(level=1).mean()
    geo = [c for c in GEO if c in gm.index]
    pho = [c for c in PHO if c in gm.index]
    has_ra = 'randaugment' in gm.index

    heights = [len(sets) for _, sets in PANELS]
    fig, axes = plt.subplots(len(PANELS), 1, figsize=(7.4, 0.78 * sum(heights) + 2.0),
                             gridspec_kw={'height_ratios': heights})
    plt.rcParams.update({'font.size': 8.5})
    bh = 0.27
    for ax, (title, sets) in zip(axes, PANELS):
        y = np.arange(len(sets))[::-1]
        vals = []
        for yi, (k, name) in zip(y, sets):
            for off, conds, col in ((bh, geo, C_GEO), (0.0, pho, C_PHO)):
                if not conds:
                    continue
                c = gm.loc[conds, k].idxmax(); v = gm.loc[c, k]
                vals.append(v)
                ax.barh(yi + off, v, height=bh, color=col, edgecolor='white', linewidth=0.5)
                ax.text(max(v, 0), yi + off, f'  {v:+.2f} {c}', va='center', ha='left', fontsize=7, color=TEXT)
            if has_ra:  # reference on its own (grey) bar, so it never overlaps the family labels
                ra = gm.loc['randaugment', k]; vals.append(ra)
                ax.barh(yi - bh, ra, height=bh, color=C_RA, edgecolor='white', linewidth=0.5)
                ax.text(max(ra, 0), yi - bh, f'  {ra:+.2f} RandAugment', va='center', ha='left', fontsize=7,
                        color=TEXT2)
        lo, hi = min(0, min(vals)), max(vals)
        ax.set_xlim(lo - 0.05 * (hi - lo), hi + 0.45 * (hi - lo))  # room for the labels
        ax.set_yticks(y, [n for _, n in sets], fontsize=8.5, color=TEXT)
        ax.tick_params(axis='y', length=0)
        ax.tick_params(axis='x', labelsize=7.5, colors=TEXT2)
        ax.axvline(0, color=TEXT2, linewidth=0.8)
        ax.grid(axis='x', color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        for side in ('top', 'right', 'left'):
            ax.spines[side].set_visible(False)
        ax.set_title(title, fontsize=9, color=TEXT, loc='left')
    rep = 'grayscale' if args.suffix == '_gray' else 'RGB'
    axes[-1].set_xlabel(f'R@1 change vs. no augmentation (points, {rep} input, mean over 3 seeds)', color=TEXT2)
    fig.suptitle(f'{rep.capitalize() if rep == "grayscale" else rep} input', x=0.01, ha='left', fontsize=10, fontweight='bold', color=TEXT)
    handles = [Patch(color=C_GEO, label='Best geometric (single or mixed)'),
               Patch(color=C_PHO, label='Best photometric (single or mixed)')]
    if has_ra:
        handles.append(Patch(color=C_RA, label='RandAugment (reference)'))
    fig.legend(handles=handles, loc='lower center', ncol=len(handles), frameon=False, fontsize=7.5,
               bbox_to_anchor=(0.5, -0.005))
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    os.makedirs('results/figures', exist_ok=True)
    stem = f'results/figures/best_per_set{args.suffix or "_rgb"}'
    fig.savefig(stem + '.pdf', bbox_inches='tight')
    fig.savefig(stem + '.png', dpi=220, bbox_inches='tight')
    print('saved', stem + '.pdf', stem + '.png')


if __name__ == '__main__':
    main()
