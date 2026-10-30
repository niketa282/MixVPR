"""Pictorial VPR pipeline: training with augmentation (top) and retrieval at test time (bottom).

Uses real images: one GSV-Cities training place and one SVOX night query with its daytime database match.

Usage:
    python results/plot_vpr_pipeline.py [--query_idx 300] [--place 0000002]
"""
import argparse
import glob
import os
import random
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle
import numpy as np
import torch
import torchvision.transforms as T
from PIL import Image
from sklearn.neighbors import NearestNeighbors

sys.path.insert(0, os.getcwd())

TEXT, TEXT2, EDGE = '#1f1f1e', '#5f5e58', '#8a8984'
C_TRAIN, C_AUG, C_NET, C_TEST, C_OK = '#2a78d6', '#eb6834', '#1baf7a', '#c98500', '#0ca30c'
GSV = '/iridisfs/geosets/gsvcities/Images/London'
SVOX = '/iridisfs/geosets/svox/images/test'


def square(img, size=256):
    w, h = img.size
    s = min(w, h)
    return img.crop(((w - s) // 2, (h - s) // 2, (w + s) // 2, (h + s) // 2)).resize((size, size))


def show(fig, img, x, y, w, h, label=None, edge=None, lw=2.0, label_color=TEXT):
    ax = fig.add_axes([x, y, w, h])
    ax.imshow(img)
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_edgecolor(edge or '#cfcec8'); s.set_linewidth(lw if edge else 0.8)
    if label:
        ax.set_title(label, fontsize=8.5, color=label_color, pad=3)
    return ax


def arrow(canvas, x0, y0, x1, y1, color=EDGE, style='-|>', ls='-'):
    canvas.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle=style, mutation_scale=14, color=color,
                                     linewidth=1.5, linestyle=ls, shrinkA=0, shrinkB=0))


def network(canvas, x, y, w, h, label='ResNet-50\n+ MixVPR'):
    canvas.add_patch(Polygon([[x, y], [x + w, y + h * 0.3], [x + w, y + h * 0.7], [x, y + h]], closed=True,
                             facecolor='#edf7f2', edgecolor=C_NET, linewidth=1.5))
    canvas.text(x + w * 0.45, y + h / 2, label, ha='center', va='center', fontsize=8.5, color=TEXT)


def descriptor(canvas, x, y, w, h, seed, n=8):
    rng = np.random.default_rng(seed)
    vals = rng.random(n)
    for i, v in enumerate(vals):
        canvas.add_patch(Rectangle((x, y + i * h / n), w, h / n,
                                   facecolor=plt.cm.Greens(0.25 + 0.7 * v), edgecolor='white', linewidth=0.6))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--query_idx', type=int, default=300)
    ap.add_argument('--place', default='0000002')
    args = ap.parse_args()
    random.seed(0); torch.manual_seed(0)

    # ---- images
    place_imgs = [square(Image.open(p).convert('RGB')) for p in sorted(glob.glob(f'{GSV}/London_{args.place}_*.jpg'))[:4]]
    src = place_imgs[0]
    persp = square(T.RandomPerspective(distortion_scale=0.2, p=1.0)(src))
    torch.manual_seed(3)
    contr = T.ColorJitter(contrast=(0.6, 0.6))(src)
    gray = T.Grayscale(num_output_channels=3)(src)

    q_paths = sorted(glob.glob(f'{SVOX}/queries_night/*.jpg'))
    db_paths = sorted(glob.glob(f'{SVOX}/gallery/*.jpg'))
    utm = lambda ps: np.array([(float(os.path.basename(p).split('@')[1]), float(os.path.basename(p).split('@')[2])) for p in ps])
    db_utm = utm(db_paths)
    q = q_paths[args.query_idx]
    nn = NearestNeighbors(n_neighbors=1).fit(db_utm)
    match = db_paths[int(nn.kneighbors(utm([q]))[1][0, 0])]
    far = [db_paths[i] for i in np.argsort(np.linalg.norm(db_utm - utm([q])[0], axis=1))[[400, 2500, 9000]]]
    q_img, m_img = square(Image.open(q).convert('RGB')), square(Image.open(match).convert('RGB'))
    others = [square(Image.open(p).convert('RGB')) for p in far]

    # ---- canvas
    fig = plt.figure(figsize=(14, 7.2))
    cv = fig.add_axes([0, 0, 1, 1]); cv.set_xlim(0, 1); cv.set_ylim(0, 1); cv.axis('off')
    cv.add_patch(FancyBboxPatch((0.008, 0.52), 0.984, 0.465, boxstyle='round,pad=0,rounding_size=0.01',
                                facecolor='#f7f9fd', edgecolor='#d8e2f1', linewidth=1))
    cv.add_patch(FancyBboxPatch((0.008, 0.015), 0.984, 0.475, boxstyle='round,pad=0,rounding_size=0.01',
                                facecolor='#fdfbf4', edgecolor='#ece3c7', linewidth=1))
    cv.text(0.018, 0.972, 'TRAINING', fontsize=11, fontweight='bold', color=C_TRAIN, va='top')
    cv.text(0.018, 0.478, 'TESTING', fontsize=11, fontweight='bold', color=C_TEST, va='top')

    # ---- training row
    s = 0.075
    cv.text(0.025, 0.905, 'GSV-Cities: 4 images of one place', fontsize=8.5, color=TEXT2, va='top')
    for i, im in enumerate(place_imgs):
        show(fig, im, 0.025 + (i % 2) * (s + 0.006), 0.73 - (i // 2) * (s * 2 + 0.012) + 0.0, s, s * 2 * 0.95 / 1.0 * 0.5 * 1.9)
    arrow(cv, 0.19, 0.745, 0.225, 0.745)

    cv.text(0.232, 0.905, 'Augmentation (training images only)', fontsize=8.5, color=C_AUG, fontweight='bold',
            va='top')
    aw = 0.085
    for i, (im, lab) in enumerate([(src, 'original'), (persp, 'geometric\n(e.g. perspective)'),
                                   (contr, 'photometric\n(e.g. contrast)')]):
        show(fig, im, 0.232 + i * (aw + 0.012), 0.6, aw, aw * 2.0, lab, edge=C_AUG if i else None,
             label_color=C_AUG if i else TEXT2)
    arrow(cv, 0.525, 0.745, 0.548, 0.745)
    cv.text(0.553, 0.905, 'Input', fontsize=8.5, color=C_TRAIN, fontweight='bold', va='top')
    show(fig, src, 0.553, 0.765, 0.05, 0.1, 'RGB', edge=C_TRAIN, lw=1.5, label_color=C_TRAIN)
    show(fig, gray, 0.553, 0.6, 0.05, 0.1, 'or grayscale', edge=C_TRAIN, lw=1.5, label_color=C_TRAIN)
    arrow(cv, 0.61, 0.745, 0.67, 0.745)
    network(cv, 0.675, 0.635, 0.085, 0.22)
    arrow(cv, 0.765, 0.745, 0.79, 0.745)
    descriptor(cv, 0.795, 0.675, 0.018, 0.14, 1)
    cv.text(0.804, 0.66, '4096-D', fontsize=7.5, color=TEXT2, ha='center', va='top')
    arrow(cv, 0.82, 0.745, 0.845, 0.745)
    cv.add_patch(FancyBboxPatch((0.85, 0.645), 0.13, 0.2, boxstyle='round,pad=0,rounding_size=0.01',
                                facecolor='white', edgecolor=C_NET, linewidth=1.2))
    cv.text(0.915, 0.82, 'Multi-Similarity loss', fontsize=8.5, color=TEXT, ha='center', va='top', fontweight='bold')
    cv.text(0.915, 0.765, 'same place → close\nother places → far', fontsize=8.2, color=TEXT2, ha='center',
            va='top', linespacing=1.6)
    cv.text(0.915, 0.67, 'best epoch on Pitts30k-val', fontsize=7.5, color=TEXT2, ha='center', va='bottom')

    # trained model handoff
    y_mid = 0.505
    cv.plot([0.915, 0.915, 0.2475], [0.645, y_mid, y_mid], color=C_NET, linewidth=1.5, linestyle=(0, (4, 3)))
    arrow(cv, 0.2475, y_mid, 0.2475, 0.365, color=C_NET, ls=(0, (4, 3)))
    cv.text(0.58, y_mid + 0.008, 'trained model (best checkpoint)', fontsize=8.5, color=C_NET, ha='center',
            va='bottom', bbox=dict(facecolor='white', edgecolor='none', pad=1))

    # ---- testing row
    show(fig, q_img, 0.03, 0.12, 0.13, 0.26, 'Query (SVOX night)', edge=C_TEST)
    cv.text(0.095, 0.085, 'no augmentation\n(grayscale models: grayscale query)', fontsize=8, color=TEXT2,
            ha='center', va='top', linespacing=1.4)
    arrow(cv, 0.168, 0.25, 0.2, 0.25)
    network(cv, 0.205, 0.14, 0.085, 0.22)
    arrow(cv, 0.295, 0.25, 0.32, 0.25)
    descriptor(cv, 0.325, 0.18, 0.018, 0.14, 2)
    arrow(cv, 0.35, 0.25, 0.385, 0.25)
    cv.add_patch(FancyBboxPatch((0.39, 0.18), 0.12, 0.14, boxstyle='round,pad=0,rounding_size=0.01',
                                facecolor='white', edgecolor=C_TEST, linewidth=1.2))
    cv.text(0.45, 0.25, 'nearest-neighbour\nsearch', fontsize=8.5, color=TEXT, ha='center', va='center',
            linespacing=1.4)
    cv.text(0.45, 0.335, 'database descriptors\n(computed once)', fontsize=7.5, color=TEXT2, ha='center',
            va='bottom')
    arrow(cv, 0.515, 0.25, 0.55, 0.25)

    db_w = 0.085
    cv.text(0.56, 0.43, 'Database (daytime), ranked by descriptor similarity (illustration)', fontsize=8.5,
            color=TEXT2, va='top')
    for i, (im, lab) in enumerate([(m_img, 'top-1'), (others[0], '2'), (others[1], '3'), (others[2], '4')]):
        ok = i == 0
        show(fig, im, 0.56 + i * (db_w + 0.012), 0.13, db_w, db_w * 2.0, lab, edge=C_OK if ok else None,
             lw=3 if ok else 2, label_color=C_OK if ok else TEXT2)
    cv.text(0.56 + db_w / 2, 0.1, '✓ within 25 m', fontsize=8.5, color=C_OK, ha='center', va='top', fontweight='bold')
    cv.text(0.56 + 2 * (db_w + 0.012), 0.065, 'Recall@1 = share of queries whose top-1 is correct',
            fontsize=8, color=TEXT2, ha='center', va='top')

    os.makedirs('results/figures', exist_ok=True)
    stem = 'results/figures/vpr_pipeline'
    fig.savefig(stem + '.pdf', bbox_inches='tight')
    fig.savefig(stem + '.png', dpi=200, bbox_inches='tight')
    print('saved', stem, '| query', os.path.basename(q), '| match', os.path.basename(match))


if __name__ == '__main__':
    main()
