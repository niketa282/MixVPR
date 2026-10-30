"""Compact versions of the gain heatmap (same data and colours as plot_gain_heatmap.py).

--layout split : two small heatmaps, general benchmarks and seasonal/weather test sets (two files)
--layout tall  : one heatmap with test sets as rows and augmentations as columns (fits a portrait page)

Usage:
    python results/plot_gain_heatmap_compact.py --layout split --scheme orangeblue
    python results/plot_gain_heatmap_compact.py --layout tall  --scheme orangeblue
"""
import argparse
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.patches import Rectangle
import pandas as pd

from plot_gain_heatmap import MIXED, N_GENERAL, SCHEMES, SETS, SINGLE, TEXT, TEXT2

CONDS = SINGLE + MIXED
SHORT = {'perspective': 'persp.', 'translate': 'transl.'}  # column labels in the tall layout


def load(seeds, suffix):
    d = pd.concat([pd.read_csv(f'results/seed{s}/test_results{suffix}.csv') for s in seeds])
    keys = [k for k, _ in SETS]
    p = d.pivot_table(index=['seed', 'condition'], columns='dataset', values='R1')[keys]
    gain = pd.concat([p.loc[s] - p.loc[s].loc['none'] for s in seeds], keys=seeds)
    mean = gain.groupby(level=1).mean().loc[CONDS]
    same = gain.groupby(level=1).agg(lambda v: (v > 0).all() or (v < 0).all()).loc[CONDS]
    return mean, same


def draw(ax, values, same, cmap, norm, vmax, fontsize):
    ax.imshow(values.values.clip(-vmax, vmax), cmap=cmap, norm=norm, aspect='auto')
    for i in range(values.shape[0]):
        for j in range(values.shape[1]):
            v = values.iat[i, j]
            label = '0.0' if round(v, 1) == 0 else f'{v:+.1f}'
            ax.text(j, i, label, ha='center', va='center', fontsize=fontsize,
                    color='white' if abs(v) > 0.55 * vmax else TEXT,
                    fontweight='bold' if same.iat[i, j] else 'normal')
            if same.iat[i, j]:
                ax.add_patch(Rectangle((j - 0.45, i - 0.43), 0.9, 0.86, fill=False, edgecolor=TEXT, linewidth=0.9))
    ax.tick_params(length=0)
    for side in ax.spines.values():
        side.set_visible(False)


def colorbar(fig, ax, cmap, norm, **kw):
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax, **kw)
    cb.set_label('R@1 change vs. none', fontsize=7.5, color=TEXT)
    cb.ax.tick_params(labelsize=7, colors=TEXT2)
    cb.outline.set_visible(False)
    cb.ax.text(0.5, 1.02, 'better', transform=cb.ax.transAxes, ha='center', va='bottom', fontsize=7, color=TEXT2)
    cb.ax.text(0.5, -0.02, 'worse', transform=cb.ax.transAxes, ha='center', va='top', fontsize=7, color=TEXT2)
    return cb


def save(fig, stem):
    os.makedirs('results/figures', exist_ok=True)
    fig.savefig(stem + '.pdf', bbox_inches='tight')
    fig.savefig(stem + '.png', dpi=220, bbox_inches='tight')
    print('saved', stem + '.pdf', stem + '.png')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--layout', choices=['split', 'tall'], default='split')
    ap.add_argument('--seeds', type=int, nargs='+', default=[190223, 1, 2])
    ap.add_argument('--suffix', default='', help="'' for RGB, '_gray' for grayscale")
    ap.add_argument('--scheme', default='orangeblue', choices=list(SCHEMES))
    ap.add_argument('--vmax', type=float, default=5.0)
    args = ap.parse_args()

    cmap = LinearSegmentedColormap.from_list(args.scheme, SCHEMES[args.scheme])
    norm = TwoSlopeNorm(vmin=-args.vmax, vcenter=0, vmax=args.vmax)
    mean, same = load(args.seeds, args.suffix)
    base = f'results/figures/gain_heatmap{args.suffix or "_rgb"}_{args.scheme}'

    if args.layout == 'split':
        groups = [('general', SETS[:N_GENERAL]), ('weather', SETS[N_GENERAL:])]
        for name, sets in groups:
            keys = [k for k, _ in sets]
            fig, ax = plt.subplots(figsize=(0.62 * len(keys) + 1.6, 3.1))
            draw(ax, mean[keys], same[keys], cmap, norm, args.vmax, fontsize=7)
            ax.axhline(len(SINGLE) - 0.5, color='white', linewidth=2.5)
            ax.set_xticks(range(len(keys)), [s for _, s in sets], rotation=35, ha='right', fontsize=7.5, color=TEXT)
            ax.set_yticks(range(len(CONDS)), CONDS, fontsize=7.5, color=TEXT)
            colorbar(fig, ax, cmap, norm, fraction=0.04, pad=0.02)
            save(fig, f'{base}_{name}')
            plt.close(fig)
    else:
        keys = [k for k, _ in SETS]
        fig, ax = plt.subplots(figsize=(4.9, 5.6))
        draw(ax, mean.T, same.T, cmap, norm, args.vmax, fontsize=6.8)
        ax.axvline(len(SINGLE) - 0.5, color='white', linewidth=2.5)
        ax.axhline(N_GENERAL - 0.5, color='white', linewidth=2.5)
        ax.set_yticks(range(len(keys)), [s for _, s in SETS], fontsize=7.5, color=TEXT)
        ax.set_xticks(range(len(CONDS)), [SHORT.get(c, c) for c in CONDS], rotation=40, ha='right', fontsize=7.5,
                      color=TEXT)
        ax.xaxis.tick_top()
        plt.setp(ax.get_xticklabels(), rotation=40, ha='left')
        colorbar(fig, ax, cmap, norm, fraction=0.045, pad=0.03)
        save(fig, f'{base}_tall')
        plt.close(fig)


if __name__ == '__main__':
    main()
