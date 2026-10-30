"""Cost vs. benefit of each single augmentation operation, one picture per input (RGB, grayscale).

Left panel: training time (GPU hours; mean over 3 seeds, whiskers = fastest/slowest seed). Right panel: R@1 gain over
no augmentation of the same input on the general (8) and seasonal & weather (6) test sets (mean over 3 seeds).
Each run used one GPU, so wall-clock hours = GPU hours; runs shared different nodes, so times are noisy.

    ~/.conda/envs/mixvpr/bin/python results/plot_cost_benefit.py
"""
import glob
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator

SEEDS = [190223, 1, 2]
GEO = ['crop', 'perspective', 'rotate', 'translate', 'shear']
PHO = ['brightness', 'contrast', 'autocontrast', 'blur']
ROWS = ['none'] + GEO + PHO
GEN = ['pitts30k_test', 'pitts250k_test', 'msls_val', 'sf_xl_small', 'tokyo247', 'amstertime', 'st_lucia', 'eynsham']
SEA = ['nordland', 'svox', 'svox_overcast', 'svox_rain', 'svox_snow', 'svox_sun']
C_GEO, C_PHO, C_NONE = '#2a78d6', '#eb6834', '#9b9a94'
C_GEN, C_SEA = '#5f5e58', '#1baf7a'
TEXT, TEXT2, GRID = '#1f1f1e', '#5f5e58', '#e4e3dd'
FS = 18
plt.rcParams.update({'font.size': FS, 'pdf.fonttype': 42})


def train_hours(inp, cond):
    hs = []
    for s in SEEDS:
        f = sorted(glob.glob(f'LOGS/{inp}_{cond}_s{s}/lightning_logs/*/events.out.tfevents.*'))[-1]
        ea = EventAccumulator(f, size_guidance={'scalars': 0}); ea.Reload()
        e = ea.Scalars('pitts30k_val/R1')
        hs.append((e[-1].wall_time - e[0].wall_time) / 3600)
    return np.array(hs)


def gains(suffix):
    d = pd.concat([pd.read_csv(f'results/seed{s}/test_results{suffix}.csv') for s in SEEDS])
    p = d.pivot_table(index=['seed', 'condition'], columns='dataset', values='R1')
    g = pd.concat([p.loc[s] - p.loc[s].loc['none'] for s in SEEDS], keys=SEEDS).groupby(level=1).mean()
    return g[GEN].mean(axis=1), g[SEA].mean(axis=1)


def style(ax):
    ax.grid(axis='x', color=GRID, linewidth=1)
    ax.set_axisbelow(True)
    ax.tick_params(colors=TEXT2, labelsize=FS - 2, length=0)
    for s in ('top', 'right', 'left'):
        ax.spines[s].set_visible(False)


def figure(inp, name, suffix):
    hours = {c: train_hours(inp, c) for c in ROWS}
    g_gen, g_sea = gains(suffix)
    y = np.arange(len(ROWS))[::-1].astype(float)
    y[1:] -= 0.4                      # gap after 'none'
    y[1 + len(GEO):] -= 0.4           # gap between geometric and photometric
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(14, 8.2), sharey=True, gridspec_kw={'width_ratios': [1, 1.25]})
    base = hours['none'].mean()
    for yi, c in zip(y, ROWS):
        h = hours[c]
        col = C_NONE if c == 'none' else (C_GEO if c in GEO else C_PHO)
        a1.barh(yi, h.mean(), 0.62, color=col)
        a1.errorbar(h.mean(), yi, xerr=[[h.mean() - h.min()], [h.max() - h.mean()]], color=TEXT2, capsize=4,
                    elinewidth=1.4)
        extra = h.mean() - base
        lab = f'{h.mean():.1f} h' if c == 'none' else f'{h.mean():.1f} h ({extra:+.1f})'.replace('-', '−')
        a1.text(h.max() + 0.15, yi, lab, va='center', fontsize=FS - 3, color=TEXT)
        if c == 'none':
            continue
        for off, val, gcol in ((0.17, g_gen[c], C_GEN), (-0.17, g_sea[c], C_SEA)):
            a2.barh(yi + off, val, 0.32, color=gcol)
            t = '0.0' if round(val, 1) == 0 else f'{val:+.1f}'.replace('-', '−')
            a2.text(max(val, 0) + 0.04, yi + off, t, va='center', fontsize=FS - 4, color=TEXT)
    a1.axvline(base, color=TEXT2, linewidth=1.3, linestyle=(0, (3, 2)))
    a1.set_xlim(0, 11.5)
    a1.set_xlabel('training time (GPU hours)', color=TEXT2)
    a1.set_title('Training cost', fontsize=FS + 2, color=TEXT, loc='left', pad=10)
    a1.set_yticks(y, ROWS, fontsize=FS - 1)
    for t, c in zip(a1.get_yticklabels(), ROWS):
        t.set_color(C_NONE if c == 'none' else (C_GEO if c in GEO else C_PHO))
    ops = ROWS[1:]
    lo = min(0, g_gen[ops].min(), g_sea[ops].min())
    hi = max(g_gen[ops].max(), g_sea[ops].max())
    a2.axvline(0, color=TEXT2, linewidth=1.2)
    a2.set_xlim(lo - 0.35, hi + 0.45)
    a2.set_xlabel('R@1 improvement (percentage points)', color=TEXT2)
    a2.set_title('Accuracy gain vs. no augmentation', fontsize=FS + 2, color=TEXT, loc='left', pad=10)
    a2.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=C_GEN), plt.Rectangle((0, 0), 1, 1, color=C_SEA)],
              labels=['General (8 sets)', 'Seasonal & weather (6 sets)'], frameon=False, fontsize=FS - 3,
              loc='upper right', bbox_to_anchor=(1.0, 1.02))
    for ax in (a1, a2):
        style(ax)
    fig.suptitle(f'{name} input', x=0.01, ha='left', fontsize=FS + 4, fontweight='bold', color=TEXT)
    fig.tight_layout(w_pad=2.5)
    stem = f'results/figures/cost_benefit_{inp}'
    fig.savefig(stem + '.pdf', bbox_inches='tight', pad_inches=0.05)
    fig.savefig(stem + '.png', dpi=300, bbox_inches='tight', pad_inches=0.05)
    plt.close(fig)
    print('saved', stem)


def main():
    os.makedirs('results/figures', exist_ok=True)
    figure('rgb', 'RGB', '')
    figure('gray', 'Grayscale', '_gray')


if __name__ == '__main__':
    main()
