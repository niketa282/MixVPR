"""Plot Pitts30k-val Recall@1 against epoch for each training condition.

Reads the TensorBoard logs written during training and saves the figure as
PDF (for LaTeX) and PNG.

Usage:
    python results/plot_val_curves.py                 # seed 190223
    python results/plot_val_curves.py --seed 1
"""
import argparse
import glob
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator

CONDITIONS = ['none', 'crop', 'perspective', 'rotate', 'translate', 'shear']
# reference categorical palette, fixed order; markers give a second encoding for print
COLORS = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300']
MARKERS = ['o', 's', '^', 'D', 'v', 'P']
TEXT_PRIMARY, TEXT_SECONDARY, GRID = '#1f1f1e', '#5f5e58', '#e4e3dd'


def val_r1(condition, seed):
    files = glob.glob(f'LOGS/rgb_{condition}_s{seed}/lightning_logs/*/events.out.tfevents.*')
    if not files:
        raise FileNotFoundError(f'No TensorBoard log for {condition}, seed {seed}')
    ea = EventAccumulator(files[0], size_guidance={'scalars': 0})
    ea.Reload()
    return [e.value * 100 for e in ea.Scalars('pitts30k_val/R1')]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', type=int, default=190223)
    parser.add_argument('--cutoff', type=int, default=30, help='epoch marked with a vertical line')
    args = parser.parse_args()

    plt.rcParams.update({'font.size': 9, 'axes.edgecolor': TEXT_SECONDARY,
                         'axes.labelcolor': TEXT_PRIMARY, 'xtick.color': TEXT_SECONDARY,
                         'ytick.color': TEXT_SECONDARY})
    fig, ax = plt.subplots(figsize=(6.0, 3.6))

    n_epochs = 0
    for cond, color, marker in zip(CONDITIONS, COLORS, MARKERS):
        r1 = val_r1(cond, args.seed)
        epochs = range(1, len(r1) + 1)  # Lightning counts from 0; plot 1-based
        n_epochs = max(n_epochs, len(r1))
        ax.plot(epochs, r1, color=color, linewidth=1.6, marker=marker, markersize=4,
                markevery=5, markeredgecolor='white', markeredgewidth=0.6, label=cond)

    ax.axvspan(args.cutoff, n_epochs + 0.5, color=GRID, alpha=0.45, linewidth=0, zorder=0)
    ax.axvline(args.cutoff, color=TEXT_SECONDARY, linewidth=1, linestyle='--', zorder=1)
    ax.text(args.cutoff + 0.6, 94.05, f'epoch {args.cutoff}', color=TEXT_SECONDARY,
            fontsize=8, va='top')

    ax.set_xlim(1, n_epochs + 0.5)
    ax.set_ylim(87.5, 94.2)
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Pitts30k-val Recall@1 (%)')
    ax.grid(axis='y', color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    leg = ax.legend(ncol=6, frameon=False, loc='lower center', bbox_to_anchor=(0.5, 1.0), fontsize=8,
                    handlelength=2.2, columnspacing=1.2)
    for t in leg.get_texts():
        t.set_color(TEXT_PRIMARY)

    fig.tight_layout()
    os.makedirs('results/figures', exist_ok=True)
    stem = f'results/figures/val_r1_vs_epoch_s{args.seed}'
    fig.savefig(stem + '.pdf')
    fig.savefig(stem + '.png', dpi=200)
    print('saved', stem + '.pdf', stem + '.png')


if __name__ == '__main__':
    main()
