"""Training cost of the single augmentation operations, RGB and grayscale.

Figure 1 (cost_val_curves): Pitts30k-val R@1 against training GPU hours, one line per operation (median over seeds;
    x = median elapsed hours at each epoch). Panels: RGB / grayscale x geometric / photometric.
Figure 2 (cost_vs_test): final test R@1 against total training GPU hours, one point per operation (mean over seeds;
    horizontal bars = min-max training time over seeds). Rows: general (8 sets) and seasonal/weather (6 sets);
    columns: RGB geometric, RGB photometric, grayscale geometric, grayscale photometric.

Each run used one GPU, so wall-clock hours = GPU hours. Runs shared heterogeneous nodes, so times are noisy.
Needs tensorboard (mixvpr env):
    ~/.conda/envs/mixvpr/bin/python results/plot_cost_curves.py
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
FAMILIES = [('Geometric', ['crop', 'perspective', 'rotate', 'translate', 'shear']),
            ('Photometric', ['brightness', 'contrast', 'autocontrast', 'blur'])]
INPUTS = [('rgb', 'RGB', ''), ('gray', 'Grayscale', '_gray')]
GEN = ['pitts30k_test', 'pitts250k_test', 'msls_val', 'sf_xl_small', 'tokyo247', 'amstertime', 'st_lucia', 'eynsham']
SEA = ['nordland', 'svox', 'svox_overcast', 'svox_rain', 'svox_snow', 'svox_sun']
GROUPS = [('General (8 sets)', GEN), ('Seasonal & weather (6 sets)', SEA)]
COL = {'none': '#1f1f1e', 'crop': '#2a78d6', 'perspective': '#eb6834', 'rotate': '#1baf7a', 'translate': '#c98500',
       'shear': '#8e44ad', 'brightness': '#2a78d6', 'contrast': '#eb6834', 'autocontrast': '#1baf7a',
       'blur': '#8e44ad'}
TEXT, TEXT2, GRID = '#1f1f1e', '#5f5e58', '#e4e3dd'
FS = 7
plt.rcParams.update({'font.size': FS, 'pdf.fonttype': 42})
OUT = 'results/figures'
# label offsets (points) where labels would collide: (input, row, condition)
LABEL_OFF = {('gray', 1, 'translate'): (-4, 3), ('gray', 1, 'crop'): (3, -7), ('gray', 0, 'crop'): (3, -6),
             ('gray', 0, 'translate'): (-4, -2)}


def val_log(inp, cond, seed):
    f = sorted(glob.glob(f'LOGS/{inp}_{cond}_s{seed}/lightning_logs/*/events.out.tfevents.*'))[-1]
    ea = EventAccumulator(f, size_guidance={'scalars': 0}); ea.Reload()
    e = ea.Scalars('pitts30k_val/R1')
    return np.array([(x.wall_time - e[0].wall_time) / 3600 for x in e]), np.array([100 * x.value for x in e])


def load_curves():
    out = {}
    for inp, _, _ in INPUTS:
        for c in ['none'] + [c for _, cs in FAMILIES for c in cs]:
            hs, vs = zip(*[val_log(inp, c, s) for s in SEEDS])
            # median over seeds: robust to the one-off collapse of RGB rotate seed 2 at epochs 12-13
            out[inp, c] = dict(h=np.median(hs, axis=0), v=np.median(vs, axis=0), total=np.array([h[-1] for h in hs]),
                               vmax=np.mean([v.max() for v in vs]), best_ep=np.median([int(np.argmax(v)) + 1 for v in vs]))
    return out


def style(ax):
    ax.grid(color=GRID, linewidth=0.5)
    ax.set_axisbelow(True)
    ax.tick_params(labelsize=FS - 1, colors=TEXT2, length=2, pad=1)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)


def save(fig, name):
    fig.savefig(f'{OUT}/{name}.pdf', bbox_inches='tight', pad_inches=0.03)
    fig.savefig(f'{OUT}/{name}.png', dpi=300, bbox_inches='tight', pad_inches=0.03)
    plt.close(fig)
    print('saved', f'{OUT}/{name}')


def fig_curves(cur):
    fig, axes = plt.subplots(2, 2, figsize=(7.0, 4.6), sharex=True, sharey=True)
    for r, (inp, iname, _) in enumerate(INPUTS):
        for c, (fname, conds) in enumerate(FAMILIES):
            ax = axes[r, c]
            for cond in ['none'] + conds:
                d = cur[inp, cond]
                ax.plot(d['h'], d['v'], color=COL[cond], linewidth=1.0 if cond != 'none' else 1.2,
                        linestyle='--' if cond == 'none' else '-', label=cond)
                ax.plot(d['h'][-1], d['v'][-1], 'o', color=COL[cond], markersize=2.5)
            ax.set_title(f'{iname}, {fname.lower()}', fontsize=FS + 0.5, color=TEXT, pad=3)
            ax.set_ylim(88, 94.5)
            style(ax)
            if r == 1:
                ax.set_xlabel('training time (GPU hours)', color=TEXT2, labelpad=1)
            if c == 0:
                ax.set_ylabel('Pitts30k-val R@1 (%)', color=TEXT2, labelpad=1)
            if r == 0:
                ax.legend(frameon=False, fontsize=FS - 1, loc='lower right', ncol=2, handlelength=1.6,
                          columnspacing=0.8)
    fig.tight_layout(h_pad=0.8, w_pad=0.8)
    save(fig, 'cost_val_curves')


def fig_test(cur):
    res = {}
    for inp, _, suf in INPUTS:
        d = pd.concat([pd.read_csv(f'results/seed{s}/test_results{suf}.csv') for s in SEEDS])
        res[inp] = d.groupby(['condition', 'dataset']).R1.mean().unstack()
    panels = [(inp, iname, fname, conds) for inp, iname, _ in INPUTS for fname, conds in FAMILIES]
    fig, axes = plt.subplots(2, 4, figsize=(7.16, 3.6), sharex=True, sharey='row')
    for r, (gname, keys) in enumerate(GROUPS):
        for c, (inp, iname, fname, conds) in enumerate(panels):
            ax = axes[r, c]
            for cond in ['none'] + conds:
                t = cur[inp, cond]['total']
                y = res[inp].loc[cond, keys].mean()
                ax.errorbar(t.mean(), y, xerr=[[t.mean() - t.min()], [t.max() - t.mean()]], fmt='o' if cond != 'none'
                            else 's', color=COL[cond], markersize=3.5, elinewidth=0.6, capsize=1.2)
                off = LABEL_OFF.get((inp, r, cond), (3, 2))
                ax.annotate(cond if cond != 'autocontrast' else 'autocontr.', (t.mean(), y), xytext=off,
                            textcoords='offset points', fontsize=FS - 1.8, color=COL[cond],
                            ha='right' if off[0] < 0 else 'left')
            style(ax)
            if r == 0:
                ax.set_title(f'{iname}\n{fname.lower()}', fontsize=FS, color=TEXT, pad=3, linespacing=1.1)
            if c == 0:
                ax.set_ylabel(f'{gname}\ntest R@1 (%)', color=TEXT2, labelpad=1, fontsize=FS - 0.5)
            if r == 1:
                ax.set_xlabel('GPU hours', color=TEXT2, labelpad=1)
    fig.tight_layout(h_pad=0.6, w_pad=0.4)
    save(fig, 'cost_vs_test')
    # numbers behind the plots
    rows = []
    for inp, iname, _ in INPUTS:
        for cond in ['none'] + [c for _, cs in FAMILIES for c in cs]:
            t = cur[inp, cond]
            rows.append(dict(input=iname, condition=cond, gpu_h_mean=t['total'].mean().round(2),
                             gpu_h_min=t['total'].min().round(2), gpu_h_max=t['total'].max().round(2),
                             best_val=round(t['vmax'], 2), best_epoch=t['best_ep'],
                             general=res[inp].loc[cond, GEN].mean().round(2),
                             seasonal=res[inp].loc[cond, SEA].mean().round(2)))
    pd.DataFrame(rows).to_csv(f'{OUT}/cost_summary.csv', index=False)
    print(pd.DataFrame(rows).to_string(index=False))


def main():
    os.makedirs(OUT, exist_ok=True)
    cur = load_curves()
    fig_curves(cur)
    fig_test(cur)


if __name__ == '__main__':
    main()
