"""Methodology overview diagram (training -> evaluation -> analysis pipeline).

Usage:
    python results/plot_methodology.py
"""
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

TEXT, TEXT2, EDGE = '#1f1f1e', '#5f5e58', '#8a8984'
FILL = {'data': '#eef3fb', 'aug': '#fdf0e9', 'model': '#edf7f2', 'eval': '#fbf6e6', 'ana': '#f2f1ee'}
ACC = {'data': '#2a78d6', 'aug': '#eb6834', 'model': '#1baf7a', 'eval': '#c98500', 'ana': '#5f5e58'}
GAP = 0.022


def box(ax, x, y, w, h, title, lines, kind, size=8.6):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0,rounding_size=0.012',
                                facecolor=FILL[kind], edgecolor=ACC[kind], linewidth=1.3))
    ax.text(x + 0.011, y + h - 0.035, title, fontsize=10, fontweight='bold', color=TEXT, va='top')
    ax.text(x + 0.011, y + h - 0.105, '\n'.join(lines), fontsize=size, color=TEXT, va='top', linespacing=1.5)


def arrow(ax, x0, y, x1):
    ax.add_patch(FancyArrowPatch((x0 + 0.003, y), (x1 - 0.003, y), arrowstyle='-|>', mutation_scale=13,
                                 color=EDGE, linewidth=1.3, shrinkA=0, shrinkB=0))


def row(ax, y, h, specs):
    """specs: list of (width, title, lines, kind); boxes laid out left to right with arrows in the gaps."""
    x, ends = 0.01, []
    for w, title, lines, kind in specs:
        box(ax, x, y, w, h, title, lines, kind)
        ends.append((x, x + w))
        x += w + GAP
    for (_, e), (s, _) in zip(ends, ends[1:]):
        arrow(ax, e, y + h / 2, s)
    return ends


def main():
    fig = plt.figure(figsize=(14, 5.6))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')

    ax.text(0.01, 0.985, 'Training — repeated for every augmentation condition × input representation × seed',
            fontsize=10, color=TEXT2, va='top')
    top = row(ax, 0.565, 0.37, [
        (0.122, 'Training data', ['GSV-Cities (23 cities)', '120 places × 4 images', 'per batch', '320 × 320 px'], 'data'),
        (0.128, 'Input', ['RGB', 'or', 'grayscale', '(3 identical channels,', 'train, val and test)'], 'data'),
        (0.262, 'Augmentation (training images only)',
         ['None (baseline)',
          'Geometric: crop, perspective, rotate, translate, shear',
          'Geometric mixed: k = 1, 2, 3 random transforms',
          'Photometric: brightness, contrast, autocontrast, blur',
          'Photometric mixed: k = 1, 2, 3 random transforms',
          'Reference: RandAugment, TrivialAugment'], 'aug'),
        (0.168, 'Model and training',
         ['ResNet-50 (ImageNet,', 'stages 1–2 frozen)', '+ MixVPR → 4096-D', 'Multi-Similarity loss',
          'SGD, 50 epochs', 'seeds 190223, 1, 2'], 'model'),
        (0.164, 'Checkpoint selection', ['Validate every epoch', 'on Pitts30k-val;', 'keep the epoch with the',
                                         'highest Recall@1'], 'model'),
    ])

    bottom = row(ax, 0.03, 0.37, [
        (0.305, 'Evaluation on 15 test sets',
         ['General: Pitts30k, Pitts250k, MSLS, SF-XL,',
          '   Tokyo 24/7, AmsterTime, St Lucia, Eynsham',
          'Seasonal / weather: Nordland, SVOX',
          '   (all, overcast, rain, snow, sun)',
          'Night: SVOX Night',
          'Correct if within 25 m (Nordland ±10 frames)'], 'eval'),
        (0.245, 'Metrics',
         ['Recall@1, @5, @10',
          'Gain: change in R@1 vs. the no-augmentation',
          '   model (same input, same seed)',
          'Mean over 3 seeds',
          'Consistent: same direction in all 3 seeds'], 'eval'),
        (0.384, 'Analyses',
         ['1  Geometric vs. photometric, for RGB and for grayscale',
          '2  RGB vs. grayscale for each augmentation (interaction)',
          '3  Single vs. mixed transforms (k = 1, 2, 3)',
          '4  Comparison with RandAugment / TrivialAugment',
          '5  Strength sweep: perspective and contrast (RGB)',
          '6  Night analysis: colour statistics and test-time',
          '   white balance / brightness / grayscale'], 'ana'),
    ])

    # right-angled connector: checkpoint box (top right) -> evaluation box (bottom left)
    x_from = (top[-1][0] + top[-1][1]) / 2
    x_to = (bottom[0][0] + bottom[0][1]) / 2
    y_mid = 0.483
    ax.plot([x_from, x_from, x_to], [0.565, y_mid, y_mid], color=EDGE, linewidth=1.3, linestyle=(0, (4, 3)))
    ax.add_patch(FancyArrowPatch((x_to, y_mid), (x_to, 0.40 + 0.003), arrowstyle='-|>', mutation_scale=13,
                                 color=EDGE, linewidth=1.3, linestyle=(0, (4, 3)), shrinkA=0, shrinkB=0))
    ax.text((x_from + x_to) / 2, y_mid + 0.012, 'best checkpoint of every run is evaluated', fontsize=8.5,
            color=TEXT2, ha='center', va='bottom')

    os.makedirs('results/figures', exist_ok=True)
    stem = 'results/figures/methodology_overview'
    fig.savefig(stem + '.pdf', bbox_inches='tight')
    fig.savefig(stem + '.png', dpi=220, bbox_inches='tight')
    print('saved', stem + '.pdf', stem + '.png')


if __name__ == '__main__':
    main()
