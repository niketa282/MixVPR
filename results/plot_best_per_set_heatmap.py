"""One-column version of best_per_set_combined: a coloured table of R@1 gains per test set.

Columns: best geometric, best photometric (single or mixed) and RandAugment, for RGB and grayscale input. The
largest of the three per input is in bold. Colour is clipped at CLIP points so night does not wash out the rest.

Usage:
    python results/plot_best_per_set_heatmap.py
"""
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
import numpy as np
import pandas as pd

SEEDS = [190223, 1, 2]
GEO = ['crop', 'perspective', 'rotate', 'translate', 'shear', 'geo_k1', 'geo_k2', 'geo_k3']
PHO = ['brightness', 'contrast', 'autocontrast', 'blur', 'phot_k1', 'phot_k2', 'phot_k3']
SETS = [('pitts30k_test', 'Pitts30k'), ('pitts250k_test', 'Pitts250k'), ('msls_val', 'MSLS'),
        ('sf_xl_small', 'SF-XL'), ('tokyo247', 'Tokyo 24/7'), ('amstertime', 'AmsterTime'), ('st_lucia', 'St Lucia'),
        ('eynsham', 'Eynsham'), ('nordland', 'Nordland'), ('svox', 'SVOX (all)'), ('svox_overcast', 'SVOX Overcast'),
        ('svox_rain', 'SVOX Rain'), ('svox_snow', 'SVOX Snow'), ('svox_sun', 'SVOX Sun'), ('svox_night', 'SVOX Night')]
GROUP_BREAKS = [8, 14]  # lines after general / seasonal-weather rows
COLS = ['Geo.', 'Phot.', 'RA']
CLIP = 8
TEXT, TEXT2 = '#1f1f1e', '#5f5e58'
CMAP = LinearSegmentedColormap.from_list('ob', ['#eb6834', '#ffffff', '#2a78d6'])
FS = 6
plt.rcParams.update({'font.size': FS, 'pdf.fonttype': 42})


def mean_gain(suffix):
    d = pd.concat([pd.read_csv(f'results/seed{s}/test_results{suffix}.csv') for s in SEEDS])
    p = d.pivot_table(index=['seed', 'condition'], columns='dataset', values='R1')
    return pd.concat([p.loc[s] - p.loc[s].loc['none'] for s in SEEDS], keys=SEEDS).groupby(level=1).mean()


def fmt(v):
    t = f'{v:+.1f}'
    return '0.0' if t in ('+0.0', '-0.0') else t


def main():
    M = []
    for suffix in ('', '_gray'):
        gm = mean_gain(suffix)
        M.append(np.array([[gm.loc[GEO, k].max(), gm.loc[PHO, k].max(), gm.loc['randaugment', k]] for k, _ in SETS]))
    M = np.round(np.hstack(M), 1)  # 15 x 6, rounded so bold matches the printed values
    fig, ax = plt.subplots(figsize=(3.5, 2.75))
    ax.imshow(np.clip(M, -CLIP, CLIP), cmap=CMAP, norm=TwoSlopeNorm(0, -CLIP, CLIP), aspect='auto')
    for i in range(M.shape[0]):
        for g in (0, 3):
            best = M[i, g:g + 3].max()
            for j in range(g, g + 3):
                ax.text(j, i, fmt(M[i, j]), ha='center', va='center', fontsize=FS - 0.3,
                        color='white' if abs(M[i, j]) > 0.75 * CLIP else TEXT,
                        fontweight='bold' if M[i, j] == best else 'normal')
    ax.set_xticks(range(6), COLS * 2, fontsize=FS)
    ax.xaxis.tick_top()
    ax.set_yticks(range(len(SETS)), [n for _, n in SETS], fontsize=FS)
    ax.tick_params(length=0, pad=2)
    ax.axvline(2.5, color='white', linewidth=3)
    for b in GROUP_BREAKS:
        ax.axhline(b - 0.5, color='white', linewidth=2)
    for x, lab in ((1, 'RGB input'), (4, 'Grayscale input')):
        ax.text(x, -1.55, lab, ha='center', va='bottom', fontsize=FS + 0.8, fontweight='bold', color=TEXT)
    for s in ax.spines.values():
        s.set_visible(False)
    fig.tight_layout(pad=0.2)
    os.makedirs('results/figures', exist_ok=True)
    stem = 'results/figures/best_per_set_heatmap'
    fig.savefig(stem + '.pdf', bbox_inches='tight', pad_inches=0.02)
    fig.savefig(stem + '.png', dpi=300, bbox_inches='tight', pad_inches=0.02)
    print('saved', stem)


if __name__ == '__main__':
    main()
