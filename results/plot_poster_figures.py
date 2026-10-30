"""Poster versions (PNG, large fonts) of the key figures, written to results/figures/poster/.

  night_rgb_vs_gray.png   SVOX Night R@1: no aug. / best geometric / best photometric / RandAugment, RGB vs. gray
  k_lines.png             R@1 vs. number of mixed augmentations k (day mean of 14 sets | night)
  best_per_set.png        per-test-set gain table (best geometric, best photometric, RandAugment; RGB | gray)
  night_example.png       one SVOX night query in RGB and grayscale, with its day database match
  vpr_pipeline_train.png  method figures from plot_vpr_pipeline_ieee.py, re-saved at high resolution
  vpr_pipeline_test.png

Needs the mixvpr env (torch, sklearn) for the image figures:
    ~/.conda/envs/mixvpr/bin/python results/plot_poster_figures.py
"""
import glob
import os
import sys
from types import SimpleNamespace

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.patches import Patch, Rectangle
import numpy as np
import pandas as pd
from PIL import Image
from sklearn.neighbors import NearestNeighbors

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plot_vpr_pipeline_ieee as pipe

OUT = 'results/figures/poster'
SEEDS = [190223, 1, 2]
GEO = ['crop', 'perspective', 'rotate', 'translate', 'shear', 'geo_k1', 'geo_k2', 'geo_k3']
PHO = ['brightness', 'contrast', 'autocontrast', 'blur', 'phot_k1', 'phot_k2', 'phot_k3']
SETS = [('pitts30k_test', 'Pitts30k'), ('pitts250k_test', 'Pitts250k'), ('msls_val', 'MSLS'),
        ('sf_xl_small', 'SF-XL'), ('tokyo247', 'Tokyo 24/7'), ('amstertime', 'AmsterTime'), ('st_lucia', 'St Lucia'),
        ('eynsham', 'Eynsham'), ('nordland', 'Nordland'), ('svox', 'SVOX (all)'), ('svox_overcast', 'SVOX Overcast'),
        ('svox_rain', 'SVOX Rain'), ('svox_snow', 'SVOX Snow'), ('svox_sun', 'SVOX Sun'), ('svox_night', 'SVOX Night')]
DAY = [k for k, _ in SETS if k != 'svox_night']
SHORT = {'geo_k1': 'mixed k=1', 'geo_k2': 'mixed k=2', 'geo_k3': 'mixed k=3', 'phot_k1': 'mixed k=1',
         'phot_k2': 'mixed k=2', 'phot_k3': 'mixed k=3'}
C_RGB, C_GRAY = '#eb6834', '#5f5e58'
TEXT, TEXT2, GRID = '#1f1f1e', '#5f5e58', '#e4e3dd'
FS = 20
DPI = 300
plt.rcParams.update({'font.size': FS, 'pdf.fonttype': 42})


def load(suffix):
    """Mean R@1 and mean gain over no augmentation (condition x dataset), averaged over seeds."""
    d = pd.concat([pd.read_csv(f'results/seed{s}/test_results{suffix}.csv') for s in SEEDS])
    p = d.pivot_table(index=['seed', 'condition'], columns='dataset', values='R1')
    g = pd.concat([p.loc[s] - p.loc[s].loc['none'] for s in SEEDS], keys=SEEDS)
    return SimpleNamespace(abs=p.groupby(level=1).mean(), sd=p.groupby(level=1).std(), g=g.groupby(level=1).mean())


def style(ax, grid='x'):
    ax.grid(axis=grid, color=GRID, linewidth=1)
    ax.set_axisbelow(True)
    ax.tick_params(colors=TEXT2, labelsize=FS - 2)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)


def save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    fig.savefig(f'{OUT}/{name}.png', dpi=DPI, bbox_inches='tight', pad_inches=0.1, facecolor='white')
    plt.close(fig)
    print('saved', f'{OUT}/{name}.png')


def night_bars(R, G):
    rows = [('No augmentation', lambda m: 'none'), ('Best geometric', lambda m: m[GEO].idxmax()),
            ('Best photometric', lambda m: m[PHO].idxmax()), ('RandAugment', lambda m: 'randaugment')]
    fig, ax = plt.subplots(figsize=(11, 6.2))
    y = np.arange(len(rows))[::-1]
    h = 0.38
    for yi, (lab, pick) in zip(y, rows):
        for off, rep, col in ((h / 2, R, C_RGB), (-h / 2, G, C_GRAY)):
            m = rep.abs['svox_night']
            c = pick(m)
            v, e = m[c], rep.sd.loc[c, 'svox_night']
            ax.barh(yi + off, v, h, xerr=e, color=col, error_kw=dict(elinewidth=1.5, capsize=4, ecolor=TEXT2))
            tag = f'  ({SHORT.get(c, c)})' if c not in ('none', 'randaugment') else ''
            ax.text(v + e + 1.5, yi + off, f'{v:.1f}{tag}', va='center', fontsize=FS - 2, color=TEXT,
                    fontweight='bold' if c == 'none' else 'normal')
    ax.set_yticks(y, [r[0] for r in rows], fontsize=FS)
    ax.tick_params(axis='y', length=0)
    ax.set_xlim(0, 100)
    ax.set_xlabel('SVOX Night Recall@1 (%)', color=TEXT2)
    style(ax)
    ax.spines['left'].set_visible(False)
    ax.legend(handles=[Patch(color=C_RGB, label='RGB'), Patch(color=C_GRAY, label='Grayscale')], loc='upper right',
              frameon=False, fontsize=FS)
    save(fig, 'night_rgb_vs_gray')


def k_lines(R, G):
    fig, axes = plt.subplots(1, 2, figsize=(13, 6))
    for ax, (title, keys) in zip(axes, [('Day (mean of 14 test sets)', DAY), ('Night (SVOX Night)', ['svox_night'])]):
        for rep, col in ((R, C_RGB), (G, C_GRAY)):
            v = rep.abs[keys].mean(axis=1)
            for fam, ls, mk in (('geo', '-', 'o'), ('phot', '--', 's')):
                ax.plot(range(4), [v['none']] + [v[f'{fam}_k{k}'] for k in (1, 2, 3)], ls, marker=mk, color=col,
                        markersize=10, linewidth=3)
            ra = v['randaugment']
            ax.plot(4.3, ra, marker='*', color=col, markersize=24, linestyle='none')
            ax.annotate(f'{ra:.1f}', (4.3, ra), xytext=(0, -24), textcoords='offset points', ha='center',
                        fontsize=FS - 3, color=col, fontweight='bold')
        if keys != DAY:
            ax.set_ylim(0, 85)
            ax.set_yticks(range(0, 81, 20))
        ax.axvline(3.65, color=GRID, linewidth=1.5)
        ax.set_xticks([0, 1, 2, 3, 4.3], ['none', '1', '2', '3', 'RandAug.'])
        ax.set_xlim(-0.3, 4.8)
        ax.set_xlabel('number of mixed augmentations $k$', color=TEXT2)
        ax.set_title(title, fontsize=FS + 2, color=TEXT, pad=10)
        style(ax, grid='y')
    axes[0].set_ylabel('Recall@1 (%)', color=TEXT2)
    handles = [plt.Line2D([], [], color=C_RGB, linewidth=4, label='RGB'),
               plt.Line2D([], [], color=C_GRAY, linewidth=4, label='Grayscale'),
               plt.Line2D([], [], color=TEXT2, marker='o', markersize=10, linewidth=3, label='geometric'),
               plt.Line2D([], [], color=TEXT2, linestyle='--', marker='s', markersize=10, linewidth=3,
                          label='photometric')]
    fig.legend(handles=handles, loc='upper center', ncol=4, frameon=False, fontsize=FS, bbox_to_anchor=(0.5, 1.07),
               handlelength=2.6)
    fig.tight_layout(w_pad=3)
    save(fig, 'k_lines')


def best_per_set(R, G):
    M = np.round(np.hstack([np.array([[rep.g.loc[GEO, k].max(), rep.g.loc[PHO, k].max(),
                                       rep.g.loc['randaugment', k]] for k, _ in SETS]) for rep in (R, G)]), 1)
    # which condition won each Geo./Phot. cell (single op or mixed k)
    tags = {'perspective': 'persp.', 'translate': 'transl.', 'brightness': 'bright.', 'contrast': 'contr.',
            'autocontrast': 'autocontr.', 'geo_k1': 'mixed k=1', 'geo_k2': 'mixed k=2', 'geo_k3': 'mixed k=3',
            'phot_k1': 'mixed k=1', 'phot_k2': 'mixed k=2', 'phot_k3': 'mixed k=3'}
    W = np.hstack([np.array([[tags.get(c, c) for c in (rep.g.loc[GEO, k].idxmax(), rep.g.loc[PHO, k].idxmax())]
                             + [''] for k, _ in SETS]) for rep in (R, G)])
    clip = 8
    cmap = LinearSegmentedColormap.from_list('ob', ['#f3a47f', '#ffffff', '#86b4ec'])  # light, so text stays black
    fig, ax = plt.subplots(figsize=(11, 13))
    ax.imshow(np.clip(M, -clip, clip), cmap=cmap, norm=TwoSlopeNorm(0, -clip, clip), aspect='auto')
    for i in range(M.shape[0]):
        for g0 in (0, 3):
            best = M[i, g0:g0 + 3].max()
            for j in range(g0, g0 + 3):
                t = f'{M[i, j]:+.1f}'
                t = '0.0' if t in ('+0.0', '-0.0') else t
                is_best = M[i, j] == best
                ax.text(j, i - (0.12 if W[i, j] else 0), t, ha='center', va='center', fontsize=FS - 2, color=TEXT,
                        fontweight='bold' if is_best else 'normal')
                if W[i, j]:
                    ax.text(j, i + 0.24, W[i, j], ha='center', va='center', fontsize=FS - 8, color=TEXT2)
                if is_best:
                    ax.add_patch(Rectangle((j - 0.44, i - 0.4), 0.88, 0.8, fill=False, edgecolor=TEXT, linewidth=2.5))
    ax.set_xticks(range(6), ['Geo.', 'Phot.', 'RandAug.'] * 2, fontsize=FS - 1)
    ax.xaxis.tick_top()
    ax.set_yticks(range(len(SETS)), [n for _, n in SETS], fontsize=FS - 1)
    ax.tick_params(length=0, pad=6, colors=TEXT)
    ax.axvline(2.5, color='white', linewidth=8)
    for b in (8, 14):
        ax.axhline(b - 0.5, color='white', linewidth=5)
    for x, lab in ((1, 'RGB input'), (4, 'Grayscale input')):
        ax.text(x, -1.45, lab, ha='center', va='bottom', fontsize=FS + 2, fontweight='bold', color=TEXT)
    for s in ax.spines.values():
        s.set_visible(False)
    save(fig, 'best_per_set')


def night_example(query_idx=300):
    q_paths = sorted(glob.glob(f'{pipe.SVOX}/queries_night/*.jpg'))
    db_paths = sorted(glob.glob(f'{pipe.SVOX}/gallery/*.jpg'))
    utm = lambda ps: np.array([(float(os.path.basename(p).split('@')[1]), float(os.path.basename(p).split('@')[2]))
                               for p in ps])
    q = q_paths[query_idx]
    match = db_paths[int(NearestNeighbors(n_neighbors=1).fit(utm(db_paths)).kneighbors(utm([q]))[1][0, 0])]
    q_img = pipe.square(Image.open(q).convert('RGB'), 512)
    panels = [(q_img, 'Night query (RGB)', '#c98500'), (q_img.convert('L').convert('RGB'), 'Same query (grayscale)',
                                                         C_GRAY),
              (pipe.square(Image.open(match).convert('RGB'), 512), 'Database (day)', '#0ca30c')]
    fig, axes = plt.subplots(1, 3, figsize=(15, 5.6))
    for ax, (im, lab, col) in zip(axes, panels):
        ax.imshow(im)
        ax.set_xticks([]); ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_edgecolor(col); sp.set_linewidth(5)
        ax.set_title(lab, fontsize=FS + 2, color=col, fontweight='bold', pad=10)
    fig.tight_layout(w_pad=2)
    save(fig, 'night_example')


def pipeline():
    """Re-save the method figures at high resolution (they are drawn 7.16 in wide)."""
    def hi_res_save(self, stem):
        name = os.path.basename(stem)
        os.makedirs(OUT, exist_ok=True)
        self.fig.savefig(f'{OUT}/{name}.png', dpi=800, bbox_inches='tight', pad_inches=0.03, facecolor='white')
        print('saved', f'{OUT}/{name}.png')
    pipe.Canvas.save = hi_res_save
    args = SimpleNamespace(query_idx=300, place='0000002')
    pipe.training(args)
    pipe.testing(args)


def main():
    R, G = load(''), load('_gray')
    night_bars(R, G)
    k_lines(R, G)
    best_per_set(R, G)
    night_example()
    pipeline()


if __name__ == '__main__':
    main()
