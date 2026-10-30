"""Heatmap of the Recall@1 change from no augmentation, per condition and test set (mean over seeds).

Cells outlined in black: the change has the same direction in all seeds.

Usage:
    python results/plot_gain_heatmap.py                    # RGB results
    python results/plot_gain_heatmap.py --suffix _gray     # grayscale results (test_results_gray.csv)
    python results/plot_gain_heatmap.py --scheme redgreen  # red = better, green = worse
    python results/plot_gain_heatmap.py --scheme orangeblue  # orange = better, blue = worse
"""
import argparse
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.patches import Rectangle
import pandas as pd

SINGLE = ['crop', 'perspective', 'rotate', 'translate', 'shear']
MIXED = ['geo_k1', 'geo_k2', 'geo_k3']
SETS = [('pitts30k_test', 'Pitts30k'), ('pitts250k_test', 'Pitts250k'), ('msls_val', 'MSLS'),
        ('sf_xl_small', 'SF-XL'), ('tokyo247', 'Tokyo 24/7'), ('amstertime', 'AmsterTime'),
        ('st_lucia', 'St Lucia'), ('eynsham', 'Eynsham'),
        ('nordland', 'Nordland'), ('svox', 'SVOX (all)'), ('svox_night', 'SVOX Night'),
        ('svox_overcast', 'SVOX Overcast'), ('svox_rain', 'SVOX Rain'), ('svox_snow', 'SVOX Snow'),
        ('svox_sun', 'SVOX Sun')]
N_GENERAL = 8
TEXT, TEXT2 = '#1f1f1e', '#5f5e58'
# diverging colour maps, listed from worst (negative) to best (positive), neutral gray at zero
SCHEMES = {
    'bluered':  ['#a3201f', '#e34948', '#f0efec', '#2a78d6', '#104281'],   # red worse, blue better
    'redgreen': ['#0b5d1e', '#2e9a48', '#f0efec', '#e34948', '#a3201f'],   # green worse, red better
    'orangeblue': ['#104281', '#2a78d6', '#f0efec', '#eb6834', '#9e3a0e'],  # blue worse, orange better (colour-blind safe)
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, nargs='+', default=[190223, 1, 2])
    ap.add_argument('--suffix', default='', help="'' for RGB, '_gray' for grayscale")
    ap.add_argument('--vmax', type=float, default=5.0)
    ap.add_argument('--scheme', default='bluered', choices=list(SCHEMES))
    args = ap.parse_args()
    CMAP = LinearSegmentedColormap.from_list(args.scheme, SCHEMES[args.scheme])

    d = pd.concat([pd.read_csv(f'results/seed{s}/test_results{args.suffix}.csv') for s in args.seeds])
    keys = [k for k, _ in SETS]
    conds = SINGLE + MIXED
    p = d.pivot_table(index=['seed', 'condition'], columns='dataset', values='R1')[keys]
    gain = pd.concat([p.loc[s] - p.loc[s].loc['none'] for s in args.seeds], keys=args.seeds)
    mean = gain.groupby(level=1).mean().loc[conds]
    n = len(args.seeds)
    same_sign = (gain.groupby(level=1).agg(lambda v: (v > 0).all() or (v < 0).all())).loc[conds]

    fig, ax = plt.subplots(figsize=(10.5, 4.4))
    norm = TwoSlopeNorm(vmin=-args.vmax, vcenter=0, vmax=args.vmax)
    ax.imshow(mean.values.clip(-args.vmax, args.vmax), cmap=CMAP, norm=norm, aspect='auto')
    for i, c in enumerate(conds):
        for j, k in enumerate(keys):
            v = mean.loc[c, k]
            dark = abs(v) > 0.55 * args.vmax
            label = '0.0' if round(v, 1) == 0 else f'{v:+.1f}'
            ax.text(j, i, label, ha='center', va='center', fontsize=8,
                    color='white' if dark else TEXT, fontweight='bold' if same_sign.loc[c, k] else 'normal')
            if same_sign.loc[c, k]:
                ax.add_patch(Rectangle((j - 0.46, i - 0.44), 0.92, 0.88, fill=False, edgecolor='#1f1f1e',
                                       linewidth=1.1))
    # group separators: single | mixed rows, general | seasonal/weather columns
    ax.axhline(len(SINGLE) - 0.5, color='white', linewidth=3)
    ax.axvline(N_GENERAL - 0.5, color='white', linewidth=3)
    ax.set_xticks(range(len(keys)), [s for _, s in SETS], rotation=40, ha='right', fontsize=8.5, color=TEXT)
    ax.set_yticks(range(len(conds)), conds, fontsize=9, color=TEXT)
    ax.tick_params(length=0)
    for side in ax.spines.values():
        side.set_visible(False)
    ax.text((N_GENERAL - 1) / 2, -0.9, 'General benchmarks', ha='center', fontsize=9, color=TEXT2)
    ax.text(N_GENERAL + (len(keys) - N_GENERAL - 1) / 2, -0.9, 'Seasonal and weather/lighting change',
            ha='center', fontsize=9, color=TEXT2)

    sm = plt.cm.ScalarMappable(norm=norm, cmap=CMAP)
    cb = fig.colorbar(sm, ax=ax, fraction=0.025, pad=0.015)
    cb.set_label('R@1 change vs. none (points)', fontsize=8.5, color=TEXT)
    cb.ax.tick_params(labelsize=8, colors=TEXT2)
    cb.outline.set_visible(False)
    cb.ax.text(0.5, 1.02, 'better', transform=cb.ax.transAxes, ha='center', va='bottom', fontsize=8, color=TEXT2)
    cb.ax.text(0.5, -0.02, 'worse', transform=cb.ax.transAxes, ha='center', va='top', fontsize=8, color=TEXT2)

    fig.tight_layout()
    os.makedirs('results/figures', exist_ok=True)
    stem = f'results/figures/gain_heatmap{args.suffix or "_rgb"}' + ('' if args.scheme == 'bluered' else f'_{args.scheme}')
    fig.savefig(stem + '.pdf')
    fig.savefig(stem + '.png', dpi=220)
    print('saved', stem + '.pdf', stem + '.png')


if __name__ == '__main__':
    main()
