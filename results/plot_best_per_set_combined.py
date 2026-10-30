"""Per test set, RGB vs. grayscale side by side: best geometric, best photometric (single or mixed) and RandAugment.

IEEE full text width (figure*, 7.16 in). Rows: general benchmarks, seasonal/weather, night; each row of panels
shares one x-scale so RGB and grayscale can be compared directly. Bars are labelled with the gain and a short
condition name (k1-k3 = mixed with k random augmentations).

Usage:
    python results/plot_best_per_set_combined.py
"""
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
import pandas as pd

SEEDS = [190223, 1, 2]
GEO = ['crop', 'perspective', 'rotate', 'translate', 'shear', 'geo_k1', 'geo_k2', 'geo_k3']
PHO = ['brightness', 'contrast', 'autocontrast', 'blur', 'phot_k1', 'phot_k2', 'phot_k3']
SHORT = {'perspective': 'persp.', 'translate': 'transl.', 'brightness': 'bright.', 'contrast': 'contr.',
         'autocontrast': 'autocontr.', 'geo_k1': 'k1', 'geo_k2': 'k2', 'geo_k3': 'k3', 'phot_k1': 'k1',
         'phot_k2': 'k2', 'phot_k3': 'k3'}
PANELS = [
    ('General', [('pitts30k_test', 'Pitts30k'), ('pitts250k_test', 'Pitts250k'), ('msls_val', 'MSLS'),
                 ('sf_xl_small', 'SF-XL'), ('tokyo247', 'Tokyo 24/7'), ('amstertime', 'AmsterTime'),
                 ('st_lucia', 'St Lucia'), ('eynsham', 'Eynsham')]),
    ('Season/weather', [('nordland', 'Nordland'), ('svox', 'SVOX (all)'), ('svox_overcast', 'SVOX Overcast'),
                        ('svox_rain', 'SVOX Rain'), ('svox_snow', 'SVOX Snow'), ('svox_sun', 'SVOX Sun')]),
    ('Night', [('svox_night', 'SVOX Night')]),
]
C_GEO, C_PHO, C_RA = '#2a78d6', '#eb6834', '#c9c8c1'
TEXT, TEXT2, GRID = '#1f1f1e', '#5f5e58', '#e4e3dd'
FS = 6
plt.rcParams.update({'font.size': FS, 'pdf.fonttype': 42})


def mean_gain(suffix):
    d = pd.concat([pd.read_csv(f'results/seed{s}/test_results{suffix}.csv') for s in SEEDS])
    p = d.pivot_table(index=['seed', 'condition'], columns='dataset', values='R1')
    return pd.concat([p.loc[s] - p.loc[s].loc['none'] for s in SEEDS], keys=SEEDS).groupby(level=1).mean()


def fmt(v):
    t = f'{v:+.1f}'
    return '0.0' if t in ('+0.0', '-0.0') else t


def bars(gm, k):
    """[(gain, label, colour)] for best geometric, best photometric, RandAugment on test set k."""
    out = []
    for conds, col in ((GEO, C_GEO), (PHO, C_PHO)):
        c = gm.loc[conds, k].idxmax()
        out.append((gm.loc[c, k], f'{fmt(gm.loc[c, k])} {SHORT.get(c, c)}', col))
    ra = gm.loc['randaugment', k]
    out.append((ra, fmt(ra), C_RA))
    return out


def main():
    reps = [('RGB input', mean_gain('')), ('Grayscale input', mean_gain('_gray'))]
    heights = [len(s) + 0.6 for _, s in PANELS]
    fig, axes = plt.subplots(len(PANELS), 2, figsize=(7.16, 0.27 * sum(heights) + 0.45), sharey='row',
                             gridspec_kw={'height_ratios': heights})
    bh = 0.27
    for r, (group, sets) in enumerate(PANELS):
        y = np.arange(len(sets))[::-1]
        allv = [v for _, gm in reps for k, _ in sets for v, _, _ in bars(gm, k)]
        lo, hi = min(0, min(allv)), max(allv)
        for c, (rep, gm) in enumerate(reps):
            ax = axes[r, c]
            for yi, (k, _) in zip(y, sets):
                for off, (v, lab, col) in zip((bh, 0, -bh), bars(gm, k)):
                    ax.barh(yi + off, v, height=bh, color=col, edgecolor='white', linewidth=0.3)
                    ax.text(max(v, 0) + 0.01 * (hi - lo), yi + off, lab, va='center', fontsize=FS - 1,
                            color=TEXT if col != C_RA else TEXT2)
            ax.set_xlim(lo - 0.03 * (hi - lo), hi * 1.2)
            ax.set_ylim(-0.6, len(sets) - 0.4)
            ax.axvline(0, color=TEXT2, linewidth=0.6)
            ax.grid(axis='x', color=GRID, linewidth=0.5)
            ax.set_axisbelow(True)
            ax.tick_params(axis='x', labelsize=FS - 0.5, colors=TEXT2, length=2, pad=1)
            ax.tick_params(axis='y', length=0)
            for s in ('top', 'right', 'left'):
                ax.spines[s].set_visible(False)
            if r == 0:
                ax.set_title(rep, fontsize=FS + 1.5, fontweight='bold', color=TEXT, pad=10)
            ax.text(0, 1.0, group, transform=ax.transAxes, fontsize=FS + 0.5, color=TEXT2, va='bottom',
                    fontstyle='italic')
        axes[r, 0].set_yticks(y, [n for _, n in sets], fontsize=FS + 0.5, color=TEXT)
    for c in range(2):
        axes[-1, c].set_xlabel('R@1 gain over no augmentation (points)', fontsize=FS, color=TEXT2, labelpad=2)
    fig.legend(handles=[Patch(color=C_GEO, label='Best geometric'), Patch(color=C_PHO, label='Best photometric'),
                        Patch(color=C_RA, label='RandAugment (reference)')],
               loc='lower center', ncol=3, frameon=False, fontsize=FS + 0.5, bbox_to_anchor=(0.5, -0.01))
    fig.tight_layout(rect=(0, 0.025, 1, 1), h_pad=0.4, w_pad=1.5)
    os.makedirs('results/figures', exist_ok=True)
    stem = 'results/figures/best_per_set_combined'
    fig.savefig(stem + '.pdf', bbox_inches='tight', pad_inches=0.02)
    fig.savefig(stem + '.png', dpi=300, bbox_inches='tight', pad_inches=0.02)
    print('saved', stem)


if __name__ == '__main__':
    main()
