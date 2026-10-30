"""One-column line chart: R@1 vs. number of mixed augmentations k (0 = none, geo_k1-3 / phot_k1-3), RGB vs. gray.

Two panels: mean over the 14 day test sets (general + seasonal/weather) and SVOX Night. RandAugment is drawn as a
separate point at the right ('RA'). Mean over 3 seeds.

Usage:
    python results/plot_k_lines.py
"""
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

SEEDS = [190223, 1, 2]
DAY = ['pitts30k_test', 'pitts250k_test', 'msls_val', 'sf_xl_small', 'tokyo247', 'amstertime', 'st_lucia', 'eynsham',
       'nordland', 'svox', 'svox_overcast', 'svox_rain', 'svox_snow', 'svox_sun']
PANELS = [('Day (mean of 14 sets)', DAY), ('Night (SVOX Night)', ['svox_night'])]
C_RGB, C_GRAY = '#eb6834', '#5f5e58'
TEXT, TEXT2, GRID = '#1f1f1e', '#5f5e58', '#e4e3dd'
FS = 6.5
plt.rcParams.update({'font.size': FS, 'pdf.fonttype': 42})


def mean_r1(suffix):
    d = pd.concat([pd.read_csv(f'results/seed{s}/test_results{suffix}.csv') for s in SEEDS])
    return d.groupby(['condition', 'dataset']).R1.mean().unstack()


def main():
    reps = [('RGB', mean_r1(''), C_RGB), ('Gray', mean_r1('_gray'), C_GRAY)]
    fig, axes = plt.subplots(1, 2, figsize=(3.5, 1.65))
    for ax, (title, keys) in zip(axes, PANELS):
        for rep, m, col in reps:
            v = m[keys].mean(axis=1)
            for fam, ls, mk in (('geo', '-', 'o'), ('phot', '--', 's')):
                ys = [v['none']] + [v[f'{fam}_k{k}'] for k in (1, 2, 3)]
                ax.plot(range(4), ys, ls, marker=mk, color=col, markersize=2.6, linewidth=1.0)
            ax.plot(4.3, v['randaugment'], marker='*', color=col, markersize=5.5, linestyle='none')
            ax.annotate(f"{v['randaugment']:.1f}", (4.3, v['randaugment']), xytext=(0, -5.5), textcoords='offset points',
                        ha='center', va='center', fontsize=FS - 1, color=col)
        ax.axvline(3.65, color=GRID, linewidth=0.8)
        if keys == ['svox_night']:
            ax.set_ylim(0, 85)
            ax.set_yticks(range(0, 81, 20))
        ax.set_xticks([0, 1, 2, 3, 4.3], ['none', '1', '2', '3', 'RA'])
        ax.set_xlim(-0.3, 4.6)
        ax.set_xlabel('mixed augmentations $k$', fontsize=FS, color=TEXT2, labelpad=1)
        ax.set_title(title, fontsize=FS + 0.5, color=TEXT, pad=3)
        ax.grid(axis='y', color=GRID, linewidth=0.5)
        ax.set_axisbelow(True)
        ax.tick_params(labelsize=FS - 0.5, colors=TEXT2, length=2, pad=1)
        for s in ('top', 'right'):
            ax.spines[s].set_visible(False)
    axes[0].set_ylabel('R@1 (%)', fontsize=FS, color=TEXT2, labelpad=1)
    handles = [plt.Line2D([], [], color=C_RGB, linewidth=1.0, label='RGB'),
               plt.Line2D([], [], color=C_GRAY, linewidth=1.0, label='Gray'),
               plt.Line2D([], [], color=TEXT2, linestyle='-', marker='o', markersize=2.6, linewidth=1.0,
                          label='geometric'),
               plt.Line2D([], [], color=TEXT2, linestyle='--', marker='s', markersize=2.6, linewidth=1.0,
                          label='photometric')]
    fig.legend(handles=handles, loc='upper center', ncol=4, frameon=False, fontsize=FS, bbox_to_anchor=(0.5, 1.04),
               handlelength=2.2, columnspacing=1.2)
    fig.tight_layout(rect=(0, 0, 1, 0.92), w_pad=1.0)
    os.makedirs('results/figures', exist_ok=True)
    stem = 'results/figures/k_lines'
    fig.savefig(stem + '.pdf', bbox_inches='tight', pad_inches=0.02)
    fig.savefig(stem + '.png', dpi=300, bbox_inches='tight', pad_inches=0.02)
    for rep, m, _ in reps:
        for title, keys in PANELS:
            v = m[keys].mean(axis=1)
            print(rep, title, {c: round(v[c], 1) for c in ['none', 'geo_k1', 'geo_k2', 'geo_k3', 'phot_k1', 'phot_k2',
                                                              'phot_k3', 'randaugment']})


if __name__ == '__main__':
    main()
