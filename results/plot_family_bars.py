"""Bar chart: average R@1 gain per augmentation, split into test-set groups, coloured by augmentation family.

Panels: general benchmarks | seasonal & weather (without SVOX Night) | SVOX Night.
Bars: mean over seeds of the group-average gain; error bars: standard deviation over seeds.
RandAugment is drawn as a dashed reference line.

Usage:
    python results/plot_family_bars.py                 # RGB
    python results/plot_family_bars.py --suffix _gray  # grayscale
"""
import argparse
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
import pandas as pd

FAMILIES = [  # (label, conditions, colour) - categorical slots in fixed order
    ('Geometric (single)', ['crop', 'perspective', 'rotate', 'translate', 'shear'], '#2a78d6'),
    ('Geometric (mixed)', ['geo_k1', 'geo_k2', 'geo_k3'], '#1baf7a'),
    ('Photometric (single)', ['brightness', 'contrast', 'autocontrast', 'blur'], '#eb6834'),
    ('Photometric (mixed)', ['phot_k1', 'phot_k2', 'phot_k3'], '#eda100'),
]
GENERAL = ['pitts30k_test', 'pitts250k_test', 'msls_val', 'sf_xl_small', 'tokyo247', 'amstertime', 'st_lucia',
           'eynsham']
WEATHER = ['nordland', 'svox', 'svox_overcast', 'svox_rain', 'svox_snow', 'svox_sun']
NIGHT = ['svox_night']
PANELS = [('General benchmarks (8)', GENERAL), ('Seasonal & weather (6, excl. Night)', WEATHER),
          ('SVOX Night', NIGHT)]
TEXT, TEXT2, GRID = '#1f1f1e', '#5f5e58', '#e4e3dd'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, nargs='+', default=[190223, 1, 2])
    ap.add_argument('--suffix', default='', help="'' for RGB, '_gray' for grayscale")
    args = ap.parse_args()

    d = pd.concat([pd.read_csv(f'results/seed{s}/test_results{args.suffix}.csv') for s in args.seeds])
    p = d.pivot_table(index=['seed', 'condition'], columns='dataset', values='R1')
    gain = pd.concat([p.loc[s] - p.loc[s].loc['none'] for s in args.seeds], keys=args.seeds)
    present = set(gain.index.get_level_values(1))
    fams = [(lab, [c for c in conds if c in present], col) for lab, conds, col in FAMILIES]
    fams = [f for f in fams if f[1]]
    conds = [c for _, cs, _ in fams for c in cs]
    colour = {c: col for _, cs, col in fams for c in cs}

    plt.rcParams.update({'font.size': 8.5, 'axes.edgecolor': TEXT2, 'xtick.color': TEXT2, 'ytick.color': TEXT})
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 0.27 * len(conds) + 1.5), sharey=True,
                             gridspec_kw={'width_ratios': [1, 1, 1.15]})
    y = np.arange(len(conds))[::-1]
    for ax, (title, keys) in zip(axes, PANELS):
        per_seed = gain[keys].mean(axis=1).unstack(level=0)  # condition x seed
        mean, std = per_seed.mean(axis=1), per_seed.std(axis=1)
        ax.barh(y, [mean[c] for c in conds], xerr=[std[c] for c in conds], color=[colour[c] for c in conds],
                height=0.72, edgecolor='white', linewidth=0.6,
                error_kw=dict(ecolor=TEXT2, elinewidth=0.8, capsize=1.8))
        pad = 0.03 * max(1.0, float((mean.abs() + std).max()))
        for yi, c in zip(y, conds):
            v = mean[c]
            label = '0.0' if round(v, 1) == 0 else f'{v:+.1f}'
            # labels always sit right of the bar end (or of zero for negative bars), clear of the error bar
            ax.text(max(v + std[c], 0) + pad, yi, label, va='center', ha='left', fontsize=7, color=TEXT2)
        ax.axvline(0, color=TEXT2, linewidth=0.8)
        if 'randaugment' in present:
            ra = gain[keys].mean(axis=1).xs('randaugment', level=1).mean()
            ax.axvline(ra, color=TEXT, linestyle='--', linewidth=1)
            ax.text(ra, len(conds) - 0.2, f' RandAugment {ra:+.1f}', fontsize=7, color=TEXT, va='bottom',
                    ha='right' if ra > 0.6 * ax.get_xlim()[1] else 'left')
        ax.set_title(title, fontsize=9, color=TEXT, loc='left')
        ax.grid(axis='x', color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        for side in ('top', 'right'):
            ax.spines[side].set_visible(False)
        ax.set_xlabel('R@1 change vs. none (points)', color=TEXT2)
        lo, hi = ax.get_xlim()
        ax.set_xlim(min(lo, -1), hi * 1.12)
    rep = 'Grayscale' if args.suffix == '_gray' else 'RGB'
    fig.suptitle(f'{rep} input', x=0.01, ha='left', fontsize=10, fontweight='bold', color=TEXT)
    axes[0].set_yticks(y, conds)
    axes[0].tick_params(axis='y', length=0)
    handles = [Patch(color=col, label=lab) for lab, _, col in fams]
    fig.legend(handles=handles, loc='lower center', ncol=len(handles), frameon=False, fontsize=8,
               bbox_to_anchor=(0.5, -0.01))
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    os.makedirs('results/figures', exist_ok=True)
    stem = f'results/figures/family_bars{args.suffix or "_rgb"}'
    fig.savefig(stem + '.pdf', bbox_inches='tight')
    fig.savefig(stem + '.png', dpi=220, bbox_inches='tight')
    print('saved', stem + '.pdf', stem + '.png')


if __name__ == '__main__':
    main()
