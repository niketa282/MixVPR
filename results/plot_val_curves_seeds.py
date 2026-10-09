"""Pitts30k-val Recall@1 against epoch, averaged over seeds (one panel per condition).

Also prints, per condition, the best validation R@1 within the first 30 epochs and over all
epochs (mean over seeds), to support the choice of training length.

Usage:
    python results/plot_val_curves_seeds.py                       # seeds 190223 1 2
    python results/plot_val_curves_seeds.py --seeds 190223 1 2 --cutoff 30
"""
import argparse
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from plot_val_curves import CONDITIONS, COLORS, GRID, TEXT_PRIMARY, TEXT_SECONDARY, val_r1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, nargs='+', default=[190223, 1, 2])
    parser.add_argument('--cutoff', type=int, default=30, help='epoch marked with a vertical line')
    args = parser.parse_args()

    curves = {c: np.array([val_r1(c, s) for s in args.seeds]) for c in CONDITIONS}  # seeds x epochs
    n_epochs = min(v.shape[1] for v in curves.values())

    print(f'{"condition":12s} best<= {args.cutoff} ep   best<= {n_epochs} ep   gain   (mean over {len(args.seeds)} seeds)')
    for c in CONDITIONS:
        r = curves[c][:, :n_epochs]
        b_cut, b_all = r[:, :args.cutoff].max(1), r.max(1)
        print(f'{c:12s} {b_cut.mean():6.2f} ± {b_cut.std(ddof=1):.2f}   {b_all.mean():6.2f} ± {b_all.std(ddof=1):.2f}'
              f'   {np.mean(b_all - b_cut):+.2f} (max {np.max(b_all - b_cut):+.2f})')

    plt.rcParams.update({'font.size': 9, 'axes.edgecolor': TEXT_SECONDARY,
                         'axes.labelcolor': TEXT_PRIMARY, 'xtick.color': TEXT_SECONDARY,
                         'ytick.color': TEXT_SECONDARY})
    fig, axes = plt.subplots(2, 3, figsize=(7.2, 4.6), sharex=True, sharey=True)
    epochs = np.arange(1, n_epochs + 1)  # Lightning counts from 0; plot 1-based
    for ax, c, color in zip(axes.flat, CONDITIONS, COLORS):
        r = curves[c][:, :n_epochs]
        ax.axvspan(args.cutoff, n_epochs + 0.5, color=GRID, alpha=0.45, linewidth=0, zorder=0)
        ax.axvline(args.cutoff, color=TEXT_SECONDARY, linewidth=0.9, linestyle='--', zorder=1)
        for run in r:  # each seed as a thin line, median across seeds in bold
            ax.plot(epochs, run, color=color, linewidth=0.7, alpha=0.45, zorder=2)
        ax.plot(epochs, np.median(r, 0), color=color, linewidth=1.8, zorder=3)
        low = r[:, 2:].min()
        if low < 90.0:  # a run left the plotted range: say so instead of hiding it
            s_idx = int(np.argmin(r[:, 2:].min(1)))
            bad = np.where(r[s_idx, 2:] < 90.0)[0] + 3  # 1-based epochs outside the plotted range
            ax.annotate(f'seed {args.seeds[s_idx]}: drops to {low:.0f}% at\nepochs {bad[0]}-{bad[-1]}, then recovers',
                        xy=(bad.mean(), 90.05), xytext=(17, 90.6), fontsize=7, color=TEXT_SECONDARY,
                        arrowprops=dict(arrowstyle='->', color=TEXT_SECONDARY, linewidth=0.7))
        ax.set_title(c, fontsize=9, color=TEXT_PRIMARY, loc='left')
        ax.grid(axis='y', color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        for side in ('top', 'right'):
            ax.spines[side].set_visible(False)
    axes[0, 0].set_ylim(90.0, 94.2)
    axes[0, 0].set_xticks([10, 20, 30, 40, 50])
    axes[0, 0].set_xlim(1, n_epochs + 0.5)
    for ax in axes[1]:
        ax.set_xlabel('Epoch')
    for ax in axes[:, 0]:
        ax.set_ylabel('Pitts30k-val R@1 (%)')

    fig.tight_layout()
    os.makedirs('results/figures', exist_ok=True)
    stem = 'results/figures/val_r1_vs_epoch_seeds_' + '_'.join(map(str, args.seeds))
    fig.savefig(stem + '.pdf')
    fig.savefig(stem + '.png', dpi=200)
    print('saved', stem + '.pdf', stem + '.png')


if __name__ == '__main__':
    main()
