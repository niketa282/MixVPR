"""Strength sweep: R@1 gain over no augmentation vs. augmentation strength (mean +/- std over 3 seeds).

Columns: perspective (distortion scale) and contrast (+/- range around 1). Rows: mean over all 15 test sets and
SVOX Night. The default strength used in the main experiments is marked with a ring.

Usage:
    python results/plot_strength_sweep.py [--suffix _gray --geo shear --phot brightness]
"""
import argparse
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

SEEDS = [190223, 1, 2]
GEN = ['pitts30k_test', 'pitts250k_test', 'msls_val', 'sf_xl_small', 'tokyo247', 'amstertime', 'st_lucia', 'eynsham']
SEA = ['nordland', 'svox', 'svox_overcast', 'svox_rain', 'svox_snow', 'svox_sun']
ALL = GEN + SEA + ['svox_night']
SWEEPS = {  # name: (x label, [(x, condition)], default x)
    'perspective': ('perspective distortion scale',
                    [(0.1, 'perspective_0.1'), (0.2, 'perspective'), (0.3, 'perspective_0.3'),
                     (0.4, 'perspective_0.4')], 0.2),
    'contrast': ('contrast range (± around 1)',
                 [(0.2, 'contrast_0.8-1.2'), (0.4, 'contrast'), (0.6, 'contrast_0.4-1.6'),
                  (0.8, 'contrast_0.2-1.8')], 0.4),
    'shear': ('shear (± degrees)', [(2.5, 'shear_2.5'), (5, 'shear'), (7.5, 'shear_7.5'), (10, 'shear_10')], 5),
    'brightness': ('brightness range (± around 1)',
                   [(0.2, 'brightness_0.8-1.2'), (0.4, 'brightness'), (0.6, 'brightness_0.4-1.6'),
                    (0.8, 'brightness_0.2-1.8')], 0.4),
}
C_GEO, C_PHO = '#2a78d6', '#eb6834'
TEXT, TEXT2, GRID = '#1f1f1e', '#5f5e58', '#e4e3dd'
FS = 7
plt.rcParams.update({'font.size': FS, 'pdf.fonttype': 42})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--suffix', default='', help="'' for RGB, '_gray' for grayscale")
    ap.add_argument('--geo', default='perspective')
    ap.add_argument('--phot', default='contrast')
    ap.add_argument('--full', action='store_true', help='one row per results-table column (for documents)')
    args = ap.parse_args()

    d = pd.concat([pd.read_csv(f'results/seed{s}/test_results{args.suffix}.csv') for s in SEEDS])
    p = d.pivot_table(index=['seed', 'condition'], columns='dataset', values='R1')
    g = pd.concat([p.loc[s] - p.loc[s].loc['none'] for s in SEEDS], keys=SEEDS)

    if args.full:  # every column of the results table, one row each
        plt.rcParams.update({'font.size': FS + 1})
        rows = [(ALL, 'All 15 sets'), (GEN, 'General (8)'), (SEA, 'Seasonal/\nweather (6)'), (['nordland'], 'Nordland'),
                (['svox_night'], 'SVOX Night'), ('count', 'Sets improved')]
        fig, axes = plt.subplots(len(rows), 2, figsize=(6.5, 8.8), sharex='col')
    else:
        rows = [(ALL, 'All 15 sets'), (['svox_night'], 'SVOX Night')]
        fig, axes = plt.subplots(2, 2, figsize=(3.5, 2.9), sharex='col')
    gm = g.groupby(level=1).mean()
    for c, (name, col) in enumerate(((args.geo, C_GEO), (args.phot, C_PHO))):
        xlab, pts, default = SWEEPS[name]
        for r, (keys, ylab) in enumerate(rows):
            ax = axes[r, c]
            xs, ms, sds = [], [], []
            for x, cond in pts:
                if keys == 'count':
                    xs.append(x); ms.append(int((gm.loc[cond, ALL] > 0).sum())); sds.append(0.0)
                    continue
                v = g.xs(cond, level=1)[keys].mean(axis=1)  # per seed
                xs.append(x); ms.append(v.mean()); sds.append(v.std())
            ax.fill_between(xs, [m - s for m, s in zip(ms, sds)], [m + s for m, s in zip(ms, sds)], color=col,
                            alpha=0.15, linewidth=0)
            ax.plot(xs, ms, '-o', color=col, markersize=3, linewidth=1.2)
            i = [x for x, _ in pts].index(default)
            ax.plot(xs[i], ms[i], 'o', markersize=7, markerfacecolor='none', markeredgecolor=TEXT, markeredgewidth=0.8)
            for x, m in zip(xs, ms):
                t = f'{m}/15' if keys == 'count' else f'{m:+.1f}'
                ax.annotate('0.0' if t in ('+0.0', '-0.0') else t, (x, m), xytext=(0, 5), textcoords='offset points',
                            ha='center', fontsize=FS - 1.5 + (1 if args.full else 0), color=TEXT)
            if keys == 'count':
                ax.set_ylim(0, 17.5)
                ax.set_yticks([0, 5, 10, 15])
                ax.set_ylabel(ylab, fontsize=FS - 0.5 + (1 if args.full else 0), color=TEXT2, labelpad=1) if c == 0 \
                    else None
                ax.set_xlabel(xlab, fontsize=FS - 0.5 + (1 if args.full else 0), color=TEXT2, labelpad=1)
                ax.set_xticks(xs)
                span = xs[-1] - xs[0]
                ax.set_xlim(xs[0] - 0.12 * span, xs[-1] + 0.12 * span)
                ax.grid(axis='y', color=GRID, linewidth=0.5)
                ax.tick_params(labelsize=FS - 1 + (1 if args.full else 0), colors=TEXT2, length=2, pad=1)
                for s in ('top', 'right'):
                    ax.spines[s].set_visible(False)
                continue
            ax.axhline(0, color=TEXT2, linewidth=0.6)
            ax.set_xticks(xs)
            span = xs[-1] - xs[0]
            ax.set_xlim(xs[0] - 0.12 * span, xs[-1] + 0.12 * span)
            ax.grid(axis='y', color=GRID, linewidth=0.5)
            ax.set_axisbelow(True)
            ax.tick_params(labelsize=FS - 1, colors=TEXT2, length=2, pad=1)
            for s in ('top', 'right'):
                ax.spines[s].set_visible(False)
            fs = FS + (1 if args.full else 0)
            if c == 0:
                ax.set_ylabel(f'{ylab}\nR@1 gain', fontsize=fs - 0.5, color=TEXT2, labelpad=1)
            if r == 0:
                ax.set_title(name.capitalize(), fontsize=fs + 0.5, color=col, fontweight='bold', pad=4)
            if r == len(rows) - 1:
                ax.set_xlabel(xlab, fontsize=fs - 0.5, color=TEXT2, labelpad=1)
            lo, hi = min(m - s for m, s in zip(ms, sds)), max(m + s for m, s in zip(ms, sds))
            ax.set_ylim(min(lo, 0) - 0.15 * (hi - lo), hi + 0.25 * (hi - lo))
    fig.tight_layout(h_pad=0.6 if not args.full else 0.9, w_pad=1.0)
    os.makedirs('results/figures', exist_ok=True)
    stem = f'results/figures/strength_sweep{args.suffix or "_rgb"}' + ('_full' if args.full else '')
    fig.savefig(stem + '.pdf', bbox_inches='tight', pad_inches=0.02)
    fig.savefig(stem + '.png', dpi=300, bbox_inches='tight', pad_inches=0.02)
    print('saved', stem)


if __name__ == '__main__':
    main()
