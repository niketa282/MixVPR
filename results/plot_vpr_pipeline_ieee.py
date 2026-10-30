"""IEEE-sized VPR pipeline figures: training and testing as two separate figures, 7.16 in wide (figure*).

Outputs results/figures/vpr_pipeline_train.pdf/.png and vpr_pipeline_test.pdf/.png.

Usage:
    python results/plot_vpr_pipeline_ieee.py [--query_idx 300] [--place 0000002]
"""
import argparse
import glob
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle
import numpy as np
import torch
import torchvision.transforms as T
from PIL import Image
from sklearn.neighbors import NearestNeighbors

TEXT, TEXT2, EDGE = '#1f1f1e', '#5f5e58', '#8a8984'
C_TRAIN, C_AUG, C_NET, C_TEST, C_OK = '#2a78d6', '#eb6834', '#1baf7a', '#c98500', '#0ca30c'
GSV = '/iridisfs/geosets/gsvcities/Images/London'
SVOX = '/iridisfs/geosets/svox/images/test'
W = 7.16  # IEEE full text width (inches)
FS, FS_S = 7.5, 6.5
plt.rcParams.update({'font.size': FS, 'pdf.fonttype': 42})


def square(img, size=256):
    w, h = img.size
    s = min(w, h)
    return img.crop(((w - s) // 2, (h - s) // 2, (w + s) // 2, (h + s) // 2)).resize((size, size))


class Canvas:
    """Draw in inches on a figure of size (W, H)."""

    def __init__(self, h):
        self.fig = plt.figure(figsize=(W, h))
        self.h = h
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_xlim(0, W); self.ax.set_ylim(0, h); self.ax.axis('off')

    def img(self, im, x, y, s, label=None, edge=None, lw=1.6, color=TEXT2):
        a = self.fig.add_axes([x / W, y / self.h, s / W, s / self.h])
        a.imshow(im); a.set_xticks([]); a.set_yticks([])
        for sp in a.spines.values():
            sp.set_edgecolor(edge or '#cfcec8'); sp.set_linewidth(lw if edge else 0.6)
        if label:
            a.set_title(label, fontsize=FS_S, color=color, pad=2, linespacing=1.1)

    def arrow(self, x0, y0, x1, y1, color=EDGE, ls='-'):
        self.ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle='-|>', mutation_scale=9, color=color,
                                          linewidth=1.0, linestyle=ls, shrinkA=0, shrinkB=0))

    def net(self, x, y, w, h):
        self.ax.add_patch(Polygon([[x, y], [x + w, y + h * 0.28], [x + w, y + h * 0.72], [x, y + h]], closed=True,
                                  facecolor='#edf7f2', edgecolor=C_NET, linewidth=1.0))
        self.ax.text(x + w * 0.45, y + h / 2, 'ResNet-50\n+ MixVPR', ha='center', va='center', fontsize=FS_S,
                     linespacing=1.2)

    def desc(self, x, y, w, h, seed, n=7):
        v = np.random.default_rng(seed).random(n)
        for i in range(n):
            self.ax.add_patch(Rectangle((x, y + i * h / n), w, h / n, facecolor=plt.cm.Greens(0.25 + 0.7 * v[i]),
                                        edgecolor='white', linewidth=0.5))

    def card(self, x, y, w, h, color):
        self.ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0,rounding_size=0.05', facecolor='white',
                                         edgecolor=color, linewidth=1.0))

    def save(self, stem):
        self.fig.savefig(stem + '.pdf', bbox_inches='tight', pad_inches=0.02)
        self.fig.savefig(stem + '.png', dpi=300, bbox_inches='tight', pad_inches=0.02)
        print('saved', stem)


def training(args):
    place = [square(Image.open(p).convert('RGB')) for p in sorted(glob.glob(f'{GSV}/London_{args.place}_*.jpg'))[:4]]
    src = place[0]
    torch.manual_seed(0)
    persp = square(T.RandomPerspective(distortion_scale=0.2, p=1.0)(src))
    contr = T.ColorJitter(contrast=(0.6, 0.6))(src)
    gray = T.Grayscale(num_output_channels=3)(src)

    # RandAugment example (seed 2: a shear plus colour operations, showing its mix of geometric and colour ops)
    torch.manual_seed(2)
    randaug = T.RandAugment(num_ops=3, interpolation=T.InterpolationMode.BILINEAR)(src)

    c = Canvas(1.75)
    c.ax.text(0.02, 1.7, 'GSV-Cities: one place', fontsize=FS_S, color=TEXT2, va='top')
    s = 0.5
    for i, im in enumerate(place):
        c.img(im, 0.02 + (i % 2) * (s + 0.04), 0.3 + (1 - i // 2) * (s + 0.06), s)
    c.arrow(1.1, 0.83, 1.22, 0.83)

    c.ax.text(1.25, 1.7, 'Augmentation (training only)', fontsize=FS_S, color=C_AUG, fontweight='bold', va='top')
    a = 0.7
    for i, (im, lab, edge) in enumerate([(src, 'original', None), (persp, 'geometric', C_AUG),
                                         (contr, 'photometric', C_AUG), (randaug, 'RandAugment\n(reference)', TEXT2)]):
        c.img(im, 1.25 + i * (a + 0.06), 0.45, a, lab, edge=edge, color=edge or TEXT2)
    c.arrow(4.26, 0.83, 4.36, 0.83)

    c.ax.text(4.39, 1.7, 'Input', fontsize=FS_S, color=C_TRAIN, fontweight='bold', va='top')
    c.img(src, 4.39, 0.9, 0.42, 'RGB', edge=C_TRAIN, lw=1.2, color=C_TRAIN)
    c.img(gray, 4.39, 0.2, 0.42, 'or gray', edge=C_TRAIN, lw=1.2, color=C_TRAIN)
    c.arrow(4.86, 0.83, 4.96, 0.83)
    c.net(4.99, 0.42, 0.6, 0.82)
    c.arrow(5.62, 0.83, 5.72, 0.83)
    c.desc(5.74, 0.57, 0.11, 0.52, 1)
    c.ax.text(5.795, 0.52, '4096-D', fontsize=6, color=TEXT2, ha='center', va='top')
    c.arrow(5.88, 0.83, 5.99, 0.83)
    c.card(6.02, 0.46, 1.12, 0.74, C_NET)
    c.ax.text(6.58, 1.13, 'Multi-Similarity\nloss', fontsize=FS_S, fontweight='bold', ha='center', va='top',
              linespacing=1.1)
    c.ax.text(6.58, 0.83, 'same place: close\nother places: far', fontsize=6, color=TEXT2, ha='center', va='top',
              linespacing=1.3)
    c.save('results/figures/vpr_pipeline_train')


def testing(args):
    q_paths = sorted(glob.glob(f'{SVOX}/queries_night/*.jpg'))
    db_paths = sorted(glob.glob(f'{SVOX}/gallery/*.jpg'))
    utm = lambda ps: np.array([(float(os.path.basename(p).split('@')[1]), float(os.path.basename(p).split('@')[2]))
                               for p in ps])
    db_utm = utm(db_paths)
    q = q_paths[args.query_idx]
    match = db_paths[int(NearestNeighbors(n_neighbors=1).fit(db_utm).kneighbors(utm([q]))[1][0, 0])]
    far = [db_paths[i] for i in np.argsort(np.linalg.norm(db_utm - utm([q])[0], axis=1))[[400, 2500]]]
    q_img, m_img = square(Image.open(q).convert('RGB')), square(Image.open(match).convert('RGB'))
    others = [square(Image.open(p).convert('RGB')) for p in far]

    c = Canvas(1.78)
    c.img(q_img, 0.02, 0.32, 1.05, 'Query (SVOX night)', edge=C_TEST, color=TEXT)
    c.ax.text(0.545, 0.25, 'no augmentation', fontsize=6, color=TEXT2, ha='center', va='top')
    c.arrow(1.12, 0.85, 1.27, 0.85)
    c.net(1.3, 0.44, 0.62, 0.82)
    c.arrow(1.95, 0.85, 2.07, 0.85)
    c.desc(2.09, 0.59, 0.11, 0.52, 2)
    c.arrow(2.24, 0.85, 2.36, 0.85)
    c.card(2.39, 0.58, 1.0, 0.54, C_TEST)
    c.ax.text(2.89, 0.85, 'nearest-neighbour\nsearch', fontsize=FS_S, ha='center', va='center', linespacing=1.2)
    c.ax.text(2.89, 1.18, 'vs. database\ndescriptors', fontsize=6, color=TEXT2, ha='center', va='bottom',
              linespacing=1.1)
    c.arrow(3.43, 0.85, 3.57, 0.85)
    c.ax.text(3.6, 1.76, 'Database (day), ranked by similarity (illustration)', fontsize=FS_S, color=TEXT2, va='top')
    d = 1.08
    for i, (im, lab) in enumerate([(m_img, 'top-1'), (others[0], '2'), (others[1], '3')]):
        ok = i == 0
        c.img(im, 3.6 + i * (d + 0.08), 0.3, d, lab, edge=C_OK if ok else None, lw=2.2 if ok else 1.0,
              color=C_OK if ok else TEXT2)
    c.ax.text(3.6 + d / 2, 0.24, 'correct (within 25 m)', fontsize=6.5, color=C_OK, ha='center', va='top',
              fontweight='bold')
    c.save('results/figures/vpr_pipeline_test')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--query_idx', type=int, default=300)
    ap.add_argument('--place', default='0000002')
    args = ap.parse_args()
    os.makedirs('results/figures', exist_ok=True)
    training(args)
    testing(args)


if __name__ == '__main__':
    main()
