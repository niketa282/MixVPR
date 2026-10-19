"""TrivialAugment vs. RandAugment (RGB): R@1 gain over no augmentation on every test set.

Uses whichever seeds already have TrivialAugment results (works with 1, 2 or 3 seeds) and compares against
RandAugment on the same seeds. Error bars: standard deviation over seeds (only when >1 seed).

Usage:
    python results/plot_ta_vs_ra.py
"""
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
import pandas as pd

SEEDS = [190223, 1, 2]
PANELS = [
    ('General benchmarks', [('pitts30k_test', 'Pitts30k'), ('pitts250k_test', 'Pitts250k'), ('msls_val', 'MSLS'),
                            ('sf_xl_small', 'SF-XL'), ('tokyo247', 'Tokyo 24/7'), ('amstertime', 'AmsterTime'),
                            ('st_lucia', 'St Lucia'), ('eynsham', 'Eynsham')]),
    ('Seasonal & weather', [('nordland', 'Nordland'), ('svox', 'SVOX (all)'), ('svox_overcast', 'SVOX Overcast'),
                            ('svox_rain', 'SVOX Rain'), ('svox_snow', 'SVOX Snow'), ('svox_sun', 'SVOX Sun')]),
    ('Night', [('svox_night', 'SVOX Night')]),
]
POLICIES = [('randaugment', 'RandAugment', '#2a78d6'), ('trivialaugment', 'TrivialAugment', '#eb6834')]
TEXT, TEXT2, GRID = '#1f1f1e', '#5f5e58', '#e4e3dd'


def main():
    frames = [pd.read_csv(f'results/seed{s}/test_results.csv') for s in SEEDS]
    d = pd.concat(frames)
    seeds = sorted(set(d[d.condition == 'trivialaugment'].seed), key=SEEDS.index)
    seeds = [s for s in seeds if (d[(d.seed == s) & (d.condition == 'trivialaugment')].shape[0] == 15)]
    if not seeds:
        raise SystemExit('no complete TrivialAugment results yet')
    p = d[d.seed.isin(seeds)].pivot_table(index=['seed', 'condition'], columns='dataset', values='R1')
    gain = pd.concat([p.loc[s] - p.loc[s].loc['none'] for s in seeds], keys=seeds)
    mean = gain.groupby(level=1).mean()
    std = gain.groupby(level=1).std() if len(seeds) > 1 else mean * 0

    keys = [k for _, sets in PANELS for k, _ in sets]
    names = {k: n for _, sets in PANELS for k, n in sets}
    print(f'seeds used: {seeds}')
    print(f'{"test set":14s} {"RandAug":>9s} {"TrivialAug":>11s} {"TA - RA":>8s}')
    for k in keys:
        ra, ta = mean.loc['randaugment', k], mean.loc['trivialaugment', k]
        print(f'{names[k]:14s} {ra:+9.2f} {ta:+11.2f} {ta - ra:+8.2f}')
    ra_all, ta_all = mean.loc['randaugment', keys].mean(), mean.loc['trivialaugment', keys].mean()
    wins = int((mean.loc['trivialaugment', keys] > mean.loc['randaugment', keys]).sum())
    print(f'{"average":14s} {ra_all:+9.2f} {ta_all:+11.2f} {ta_all - ra_all:+8.2f}   TrivialAugment higher on {wins}/15')

    heights = [len(sets) for _, sets in PANELS]
    fig, axes = plt.subplots(len(PANELS), 1, figsize=(7.2, 0.62 * sum(heights) + 2.2),
                             gridspec_kw={'height_ratios': heights})
    bh = 0.38
    for ax, (title, sets) in zip(axes, PANELS):
        y = np.arange(len(sets))[::-1]
        vals = []
        for yi, (k, _) in zip(y, sets):
            for off, (cond, _, col) in zip((bh / 2, -bh / 2), POLICIES):
                v, e = mean.loc[cond, k], std.loc[cond, k]
                vals += [v - e, v + e]
                ax.barh(yi + off, v, height=bh, color=col, xerr=e if len(seeds) > 1 else None,
                        error_kw=dict(ecolor=TEXT2, elinewidth=0.8, capsize=1.8), edgecolor='white', linewidth=0.5)
                ax.text(max(v + e, 0), yi + off, f'  {v:+.2f}', va='center', ha='left', fontsize=7, color=TEXT)
        lo, hi = min(0, min(vals)), max(vals)
        ax.set_xlim(lo - 0.05 * (hi - lo), hi + 0.22 * (hi - lo))
        ax.set_yticks(y, [n for _, n in sets], fontsize=8.5, color=TEXT)
        ax.tick_params(axis='y', length=0)
        ax.tick_params(axis='x', labelsize=7.5, colors=TEXT2)
        ax.axvline(0, color=TEXT2, linewidth=0.8)
        ax.grid(axis='x', color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        for side in ('top', 'right', 'left'):
            ax.spines[side].set_visible(False)
        ax.set_title(title, fontsize=9, color=TEXT, loc='left')
    seed_txt = f'{len(seeds)} seed{"s" if len(seeds) > 1 else ""} ({", ".join(map(str, seeds))})'
    axes[-1].set_xlabel(f'R@1 change vs. no augmentation (points, RGB, mean over {seed_txt})', color=TEXT2)
    fig.legend(handles=[Patch(color=c, label=l) for _, l, c in POLICIES], loc='lower center', ncol=2,
               frameon=False, fontsize=8, bbox_to_anchor=(0.5, -0.005))
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    os.makedirs('results/figures', exist_ok=True)
    stem = 'results/figures/trivialaugment_vs_randaugment_rgb'
    fig.savefig(stem + '.pdf', bbox_inches='tight')
    fig.savefig(stem + '.png', dpi=220, bbox_inches='tight')
    print('saved', stem + '.pdf', stem + '.png')


if __name__ == '__main__':
    main()
