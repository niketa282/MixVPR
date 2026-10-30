"""Compact one-column summary: R@1 gain of mixed geometric, mixed photometric and RandAugment, RGB vs. grayscale,
for general benchmarks, seasonal/weather test sets and SVOX Night (separate x-scales).

With --family_mean, each family bar is the mean over all its conditions (8 geometric, 7 photometric) instead of
the single mixed setting geo_k2 / phot_k3.

Usage:
    python results/plot_family_repr_compact.py [--family_mean]
"""
import argparse
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

SEEDS = [190223, 1, 2]
GEN = ['pitts30k_test', 'pitts250k_test', 'msls_val', 'sf_xl_small', 'tokyo247', 'amstertime', 'st_lucia', 'eynsham']
SEA = ['nordland', 'svox', 'svox_overcast', 'svox_rain', 'svox_snow', 'svox_sun']
PANELS = [('General', GEN), ('Season/weather', SEA), ('Night', ['svox_night'])]
CONDS = [('geo_k2', 'Geometric\n(mixed, k=2)'), ('phot_k3', 'Photometric\n(mixed, k=3)'), ('randaugment', 'RandAugment')]
GEO = ['crop', 'perspective', 'rotate', 'translate', 'shear', 'geo_k1', 'geo_k2', 'geo_k3']
PHO = ['brightness', 'contrast', 'autocontrast', 'blur', 'phot_k1', 'phot_k2', 'phot_k3']
CONDS_FAM = [('geo', 'Geometric\n(mean of 8)'), ('pho', 'Photometric\n(mean of 7)'), ('randaugment', 'RandAugment')]
C_RGB, C_GRAY = '#eb6834', '#5f5e58'
TEXT, TEXT2, GRID = '#1f1f1e', '#5f5e58', '#e4e3dd'
plt.rcParams.update({'font.size': 7, 'pdf.fonttype': 42})


def gains(suffix):
    d = pd.concat([pd.read_csv(f'results/seed{s}/test_results{suffix}.csv') for s in SEEDS])
    p = d.pivot_table(index=['seed', 'condition'], columns='dataset', values='R1')
    g = pd.concat([p.loc[s] - p.loc[s].loc['none'] for s in SEEDS], keys=SEEDS)
    fam = pd.concat({(s, f): g.loc[s].loc[c].mean() for s in SEEDS for f, c in (('geo', GEO), ('pho', PHO))}).unstack()
    g = pd.concat([g, fam])
    # per-seed group mean, then mean / std over seeds
    out = {}
    for name, keys in PANELS:
        per_seed = g[keys].mean(axis=1).unstack(level=0)
        out[name] = (per_seed.mean(axis=1), per_seed.std(axis=1))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--family_mean', action='store_true')
    args = ap.parse_args()
    conds = CONDS_FAM if args.family_mean else CONDS
    R, G = gains(''), gains('_gray')
    fig, axes = plt.subplots(1, 3, figsize=(3.5, 2.05), sharey=True, gridspec_kw={'width_ratios': [1, 1, 1.25]})
    y = np.arange(len(conds))[::-1]
    h = 0.36
    for ax, (name, _) in zip(axes, PANELS):
        (mr, sr), (mg, sg) = R[name], G[name]
        vals = []
        for yi, (c, _) in zip(y, conds):
            for off, m, s, col in ((h / 2, mr, sr, C_RGB), (-h / 2, mg, sg, C_GRAY)):
                ax.barh(yi + off, m[c], h, xerr=s[c], color=col,
                        error_kw=dict(elinewidth=0.5, capsize=1.2, ecolor=TEXT2))
                vals += [m[c] + s[c], m[c] - s[c]]
                ax.text(max(m[c] + s[c], 0) + 0.04 * max(vals), yi + off, f'{m[c]:.1f}', va='center', fontsize=5.6,
                        color=TEXT)
        ax.set_xlim(min(0, min(vals)) * 1.1, max(vals) * 1.35)
        ax.axvline(0, color=TEXT2, linewidth=0.6)
        ax.set_title(name, fontsize=7, color=TEXT, pad=3)
        ax.grid(axis='x', color=GRID, linewidth=0.5)
        ax.set_axisbelow(True)
        ax.tick_params(axis='x', labelsize=6, colors=TEXT2, length=2)
        ax.tick_params(axis='y', length=0)
        for s in ('top', 'right', 'left'):
            ax.spines[s].set_visible(False)
    axes[0].set_yticks(y, [lab for _, lab in conds], fontsize=6.5)
    axes[1].set_xlabel('R@1 gain over no augmentation (points)', fontsize=6.5, color=TEXT2, labelpad=3)
    fig.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=C_RGB), plt.Rectangle((0, 0), 1, 1, color=C_GRAY)],
               labels=['RGB', 'Grayscale'], loc='upper center', ncol=2, frameon=False, fontsize=6.5,
               bbox_to_anchor=(0.6, 1.02))
    fig.tight_layout(rect=(0, 0, 1, 0.93), w_pad=0.6)
    os.makedirs('results/figures', exist_ok=True)
    stem = 'results/figures/family_repr_compact' + ('_familymean' if args.family_mean else '')
    fig.savefig(stem + '.pdf', bbox_inches='tight', pad_inches=0.02)
    fig.savefig(stem + '.png', dpi=300, bbox_inches='tight', pad_inches=0.02)
    print('saved', stem)


if __name__ == '__main__':
    main()
