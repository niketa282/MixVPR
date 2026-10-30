"""Heatmap of grayscale minus RGB Recall@1, per condition (incl. none) and test set, mean over seeds.

Positive (orange): the grayscale model scores higher than the RGB model trained with the same augmentation.
Outlined: same direction in all seeds (grayscale and RGB runs with the same seed compared).

Usage:
    PYTHONPATH=results python results/plot_rgb_vs_gray.py
"""
import argparse

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
import pandas as pd

from plot_gain_heatmap import MIXED, N_GENERAL, SCHEMES, SETS, SINGLE, TEXT, TEXT2
from plot_gain_heatmap_compact import SHORT, draw, save

CONDS = ['none'] + SINGLE + MIXED


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, nargs='+', default=[190223, 1, 2])
    ap.add_argument('--vmax', type=float, default=8.0)
    ap.add_argument('--scheme', default='orangeblue', choices=list(SCHEMES))
    args = ap.parse_args()

    keys = [k for k, _ in SETS]
    piv = {}
    for suffix in ('', '_gray'):
        d = pd.concat([pd.read_csv(f'results/seed{s}/test_results{suffix}.csv') for s in args.seeds])
        piv[suffix] = d.pivot_table(index=['seed', 'condition'], columns='dataset', values='R1')[keys]
    diff = pd.concat([piv['_gray'].loc[s].loc[CONDS] - piv[''].loc[s].loc[CONDS] for s in args.seeds],
                     keys=args.seeds)
    mean = diff.groupby(level=1).mean().loc[CONDS]
    same = diff.groupby(level=1).agg(lambda v: (v > 0).all() or (v < 0).all()).loc[CONDS]

    cmap = LinearSegmentedColormap.from_list(args.scheme, SCHEMES[args.scheme])
    norm = TwoSlopeNorm(vmin=-args.vmax, vcenter=0, vmax=args.vmax)
    fig, ax = plt.subplots(figsize=(5.3, 5.6))
    draw(ax, mean.T, same.T, cmap, norm, args.vmax, fontsize=6.6)
    ax.axvline(0.5, color='white', linewidth=2.5)
    ax.axvline(len(SINGLE) + 0.5, color='white', linewidth=2.5)
    ax.axhline(N_GENERAL - 0.5, color='white', linewidth=2.5)
    ax.set_yticks(range(len(keys)), [s for _, s in SETS], fontsize=7.5, color=TEXT)
    ax.set_xticks(range(len(CONDS)), [SHORT.get(c, c) for c in CONDS], fontsize=7.5, color=TEXT)
    ax.xaxis.tick_top()
    plt.setp(ax.get_xticklabels(), rotation=40, ha='left')

    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax, fraction=0.045, pad=0.03)
    cb.set_label(f'Grayscale − RGB R@1 (capped at ±{args.vmax:g})', fontsize=7.5, color=TEXT)
    cb.ax.tick_params(labelsize=7, colors=TEXT2)
    cb.outline.set_visible(False)
    cb.ax.text(0.5, 1.02, 'gray\nbetter', transform=cb.ax.transAxes, ha='center', va='bottom', fontsize=7,
               color=TEXT2)
    cb.ax.text(0.5, -0.02, 'RGB\nbetter', transform=cb.ax.transAxes, ha='center', va='top', fontsize=7,
               color=TEXT2)
    save(fig, f'results/figures/gray_minus_rgb_{args.scheme}')


if __name__ == '__main__':
    main()
