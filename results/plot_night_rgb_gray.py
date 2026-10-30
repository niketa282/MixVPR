"""SVOX Night: absolute R@1 for RGB vs. grayscale (no aug., best geometric, best photometric, RandAugment).

One IEEE column wide (3.5 in). Best geometric/photometric = condition with the highest mean night R@1 for that
representation (named in the labels).

Usage:
    python results/plot_night_rgb_gray.py
"""
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

SEEDS = [190223, 1, 2]
GEO = ['crop', 'perspective', 'rotate', 'translate', 'shear', 'geo_k1', 'geo_k2', 'geo_k3']
PHO = ['brightness', 'contrast', 'autocontrast', 'blur', 'phot_k1', 'phot_k2', 'phot_k3']
C_RGB, C_GRAY = '#eb6834', '#5f5e58'
TEXT, TEXT2, GRID = '#1f1f1e', '#5f5e58', '#e4e3dd'
plt.rcParams.update({'font.size': 7.5, 'pdf.fonttype': 42})


def night(suffix):
    d = pd.concat([pd.read_csv(f'results/seed{s}/test_results{suffix}.csv') for s in SEEDS])
    d = d[d.dataset == 'svox_night']
    m = d.groupby('condition').R1.mean()
    sd = d.groupby('condition').R1.std()
    return m, sd


def main():
    (mr, sr), (mg, sg) = night(''), night('_gray')
    rows = []
    for label, pick in [('No augmentation', lambda m: 'none'), ('Best geometric', lambda m: m[GEO].idxmax()),
                        ('Best photometric', lambda m: m[PHO].idxmax()), ('RandAugment', lambda m: 'randaugment')]:
        cr, cg = pick(mr), pick(mg)
        rows.append((label, mr[cr], sr[cr], cr, mg[cg], sg[cg], cg))
    fig, ax = plt.subplots(figsize=(3.5, 2.15))
    y = np.arange(len(rows))[::-1]
    h = 0.36
    for yi, (lab, vr, er, cr, vg, eg, cg) in zip(y, rows):
        ax.barh(yi + h / 2, vr, h, xerr=er, color=C_RGB, error_kw=dict(elinewidth=0.6, capsize=1.5, ecolor=TEXT2))
        ax.barh(yi - h / 2, vg, h, xerr=eg, color=C_GRAY, error_kw=dict(elinewidth=0.6, capsize=1.5, ecolor=TEXT2))
        tag = lambda c: '' if c in ('none', 'randaugment') else f' ({c})'
        ax.text(vr + er + 1, yi + h / 2, f'{vr:.1f}{tag(cr)}', va='center', fontsize=6.3, color=TEXT)
        ax.text(vg + eg + 1, yi - h / 2, f'{vg:.1f}{tag(cg)}', va='center', fontsize=6.3, color=TEXT)
    ax.set_yticks(y, [r[0] for r in rows])
    ax.tick_params(axis='y', length=0)
    ax.set_xlim(0, 100)
    ax.set_xlabel('SVOX Night Recall@1 (%)', color=TEXT2)
    ax.grid(axis='x', color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    for s in ('top', 'right', 'left'):
        ax.spines[s].set_visible(False)
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=C_RGB), plt.Rectangle((0, 0), 1, 1, color=C_GRAY)],
              labels=['RGB', 'Grayscale'], loc='upper right', frameon=False, fontsize=6.8)
    fig.tight_layout()
    os.makedirs('results/figures', exist_ok=True)
    stem = 'results/figures/night_rgb_vs_gray'
    fig.savefig(stem + '.pdf', bbox_inches='tight', pad_inches=0.02)
    fig.savefig(stem + '.png', dpi=300, bbox_inches='tight', pad_inches=0.02)
    for r in rows:
        print(f'{r[0]:18s} RGB {r[1]:5.1f} ({r[3]})  Gray {r[4]:5.1f} ({r[6]})')


if __name__ == '__main__':
    main()
