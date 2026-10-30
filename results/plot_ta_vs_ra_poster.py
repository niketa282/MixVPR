"""Poster figure: TrivialAugment vs. RandAugment (RGB or grayscale input, seeds 190223, 1 and 2).

Two figures: Pitts30k-val R@1 against training time (ta_vs_ra_training) and a slope chart of test R@1 from RandAugment to
TrivialAugment per test condition, with the no-augmentation level on Nordland marked.
Large fonts for an A0/A1 poster. Needs tensorboard (mixvpr env).

Usage:
    ~/.conda/envs/mixvpr/bin/python results/plot_ta_vs_ra_poster.py [--input gray]
"""
import argparse
import glob
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator

SEEDS = [190223, 1, 2]
GEN = ['pitts30k_test', 'pitts250k_test', 'msls_val', 'sf_xl_small', 'tokyo247', 'amstertime', 'st_lucia', 'eynsham']
WEA = ['svox_overcast', 'svox_rain', 'svox_snow', 'svox_sun']
GROUPS = [('Weather', WEA), ('General', GEN), ('Nordland', ['nordland']), ('Night', ['svox_night'])]
POL = [('randaugment', 'RandAugment', '#2a78d6'), ('trivialaugment', 'TrivialAugment', '#eb6834')]
TEXT, TEXT2, GRID, MUTED, ALERT = '#1f1f1e', '#5f5e58', '#e4e3dd', '#9b9a94', '#c0392b'
FS = 18
plt.rcParams.update({'font.size': FS, 'pdf.fonttype': 42})
# vertical label nudges (R@1 units) where right-hand labels would collide; 'none' = no-augmentation label
LABEL_DY = {'gray': {'Night': 1.0, 'Nordland': -1.0, 'none': -2.2}}


def val_curve(inp, cond):
    """Mean over seeds of (hours since first validation, val R@1 %) per epoch."""
    hs, rs = [], []
    for s in SEEDS:
        f = glob.glob(f'LOGS/{inp}_{cond}_s{s}/lightning_logs/*/events.out.tfevents.*')[0]
        ea = EventAccumulator(f, size_guidance={'scalars': 0}); ea.Reload()
        e = ea.Scalars('pitts30k_val/R1')
        hs.append([(x.wall_time - e[0].wall_time) / 3600 for x in e]); rs.append([100 * x.value for x in e])
    return np.mean(hs, axis=0), np.mean(rs, axis=0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', choices=['rgb', 'gray'], default='rgb')
    inp = ap.parse_args().input
    suffix = '' if inp == 'rgb' else '_gray'
    d = pd.concat([pd.read_csv(f'results/seed{s}/test_results{suffix}.csv') for s in SEEDS])
    r = d[d.seed.isin(SEEDS)].groupby(['condition', 'dataset']).R1.mean().unstack()

    os.makedirs('results/figures', exist_ok=True)

    def style(ax):
        ax.grid(axis='y', color=GRID, linewidth=1)
        ax.set_axisbelow(True)
        ax.tick_params(colors=TEXT2, labelsize=FS - 1)
        for s in ('top', 'right'):
            ax.spines[s].set_visible(False)

    def save(fig, stem):
        fig.tight_layout()
        fig.savefig(stem + '.pdf', bbox_inches='tight', pad_inches=0.05)
        fig.savefig(stem + '.png', dpi=300, bbox_inches='tight', pad_inches=0.05)
        plt.close(fig)
        print('saved', stem)

    # ---- figure 1: training
    fig, a1 = plt.subplots(figsize=(7.2, 5.6))
    for cond, name, col in POL:
        h, v = val_curve(inp, cond)
        a1.plot(h, v, color=col, linewidth=3, label=name)
        a1.plot(h[-1], v[-1], 'o', color=col, markersize=9)
        a1.annotate(f'{h[-1]:.1f} h', (h[-1], v[-1]), xytext=(0, -26), textcoords='offset points', ha='center',
                    fontsize=FS, color=col, fontweight='bold')
    a1.set_ylim(86, 94.5)
    a1.set_xlabel('training time (GPU hours)', color=TEXT2)
    a1.set_ylabel('validation R@1 (%)', color=TEXT2)
    a1.legend(frameon=False, loc='lower right', fontsize=FS - 1, bbox_to_anchor=(1.0, 0.12))
    style(a1)
    save(fig, f'results/figures/ta_vs_ra_training{suffix}')

    # ---- figure 2: testing slope chart (original style)
    fig, a2 = plt.subplots(figsize=(8.0, 5.6))
    x0, x1 = 0, 1.4
    for lab, ks in GROUPS:
        va, vt = r.loc['randaugment', ks].mean(), r.loc['trivialaugment', ks].mean()
        drop = vt - va
        col = ALERT if lab == 'Nordland' else (TEXT if lab == 'Night' else MUTED)
        lw = 3.5 if col != MUTED else 2.5
        a2.plot([x0, x1], [va, vt], color=col, linewidth=lw, marker='o', markersize=9)
        a2.text(x0 - 0.1, va, f'{va:.1f}', ha='right', va='center', fontsize=FS - 1, color=col)
        a2.text(x1 + 0.1, vt + LABEL_DY.get(inp, {}).get(lab, 0), f'{vt:.1f}  {lab} ({drop:+.1f})'.replace('-', '\u2212'), ha='left', va='center',
                fontsize=FS - 1, color=col, fontweight='bold' if col != MUTED else 'normal')
    nb = r.loc['none', 'nordland']
    a2.plot([x1 - 0.08, x1 + 0.08], [nb, nb], color=ALERT, linewidth=2.5, linestyle=(0, (2, 1.5)))
    a2.text(x1 + 0.12, nb + LABEL_DY.get(inp, {}).get('none', 0), f'{nb:.1f}  no augmentation', ha='left', va='center', fontsize=FS - 3, color=ALERT,
            fontstyle='italic')
    a2.set_xticks([x0, x1], ['RandAugment', 'TrivialAugment'])
    a2.set_xlim(-0.55, 3.1)
    a2.set_ylim(40, 97)
    a2.set_ylabel('test R@1 (%)', color=TEXT2)
    style(a2)
    a2.spines['bottom'].set_visible(False)
    a2.tick_params(axis='x', length=0, labelsize=FS, labelcolor=TEXT)
    save(fig, f'results/figures/ta_vs_ra_testing{suffix}')


if __name__ == '__main__':
    main()
