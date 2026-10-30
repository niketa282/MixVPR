"""Single-strip VPR pipeline (training | testing), IEEE full text width (figure*), ~1.3 in tall.

Reuses the images and drawing helpers of plot_vpr_pipeline_ieee.py.
Outputs results/figures/vpr_pipeline_compact.pdf/.png.

Usage:
    python results/plot_vpr_pipeline_compact.py [--query_idx 300] [--place 0000002]
"""
import argparse
import glob
import os
import sys

import numpy as np
import torch
import torchvision.transforms as T
from PIL import Image
from sklearn.neighbors import NearestNeighbors

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_vpr_pipeline_ieee import (C_AUG, C_NET, C_OK, C_TEST, C_TRAIN, EDGE, FS_S, GSV, SVOX, TEXT, TEXT2,
                                    Canvas, square)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--query_idx', type=int, default=300)
    ap.add_argument('--place', default='0000002')
    args = ap.parse_args()

    src = square(Image.open(sorted(glob.glob(f'{GSV}/London_{args.place}_*.jpg'))[0]).convert('RGB'))
    torch.manual_seed(0)
    persp = square(T.RandomPerspective(distortion_scale=0.2, p=1.0)(src))
    contr = T.ColorJitter(contrast=(0.6, 0.6))(src)
    gray = T.Grayscale(num_output_channels=3)(src)
    torch.manual_seed(2)
    randaug = T.RandAugment(num_ops=3, interpolation=T.InterpolationMode.BILINEAR)(src)

    q_paths = sorted(glob.glob(f'{SVOX}/queries_night/*.jpg'))
    db_paths = sorted(glob.glob(f'{SVOX}/gallery/*.jpg'))
    utm = lambda ps: np.array([(float(os.path.basename(p).split('@')[1]), float(os.path.basename(p).split('@')[2]))
                               for p in ps])
    q = q_paths[args.query_idx]
    match = db_paths[int(NearestNeighbors(n_neighbors=1).fit(utm(db_paths)).kneighbors(utm([q]))[1][0, 0])]
    q_img, m_img = square(Image.open(q).convert('RGB')), square(Image.open(match).convert('RGB'))

    c = Canvas(1.3)
    yc = 0.55  # vertical centre of the flow
    # (a) training
    c.ax.text(0.02, 1.28, '(a) Training', fontsize=FS_S + 0.5, fontweight='bold', color=TEXT, va='top')
    a = 0.6
    for i, (im, lab, edge) in enumerate([(src, 'original', None), (persp, 'geometric', C_AUG),
                                         (contr, 'photometric', C_AUG), (randaug, 'RandAugment', TEXT2)]):
        c.img(im, 0.02 + i * (a + 0.05), yc - a / 2, a, lab, edge=edge, color=edge or TEXT2)
    c.arrow(2.62, yc, 2.72, yc)
    s = 0.34
    c.img(src, 2.75, yc + 0.03, s, edge=C_TRAIN, lw=1.0)
    c.img(gray, 2.75, yc - s - 0.03, s, edge=C_TRAIN, lw=1.0)
    c.ax.text(2.75 + s / 2, yc + s + 0.06, 'RGB / gray', fontsize=6, color=C_TRAIN, ha='center', va='bottom')
    c.arrow(3.12, yc, 3.22, yc)
    c.net(3.25, yc - 0.33, 0.55, 0.66)
    c.arrow(3.83, yc, 3.93, yc)
    c.card(3.96, yc - 0.27, 0.78, 0.54, C_NET)
    c.ax.text(4.35, yc + 0.13, 'Multi-Similarity\nloss', fontsize=6, fontweight='bold', ha='center', va='center',
              linespacing=1.05)
    c.ax.text(4.35, yc - 0.14, 'same place: close\nothers: far', fontsize=5.3, color=TEXT2, ha='center',
              va='center', linespacing=1.1)
    c.ax.plot([4.86, 4.86], [0.08, 1.25], color=EDGE, linewidth=0.6, linestyle=(0, (3, 2)))
    # (b) testing
    c.ax.text(4.95, 1.28, '(b) Testing (no augmentation)', fontsize=FS_S + 0.5, fontweight='bold', color=TEXT,
              va='top')
    b = 0.68
    c.img(q_img, 4.95, yc - b / 2, b, 'night query', edge=C_TEST, color=TEXT2)
    c.arrow(5.66, yc, 5.76, yc)
    c.net(5.79, yc - 0.31, 0.57, 0.62)
    c.arrow(6.38, yc, 6.44, yc)
    c.img(m_img, 6.46, yc - b / 2, b, 'top-1 (day db)', edge=C_OK, lw=1.8, color=C_OK)
    c.ax.text(6.46 + b / 2, yc - b / 2 - 0.04, 'correct if $\\leq$25 m', fontsize=5.5, color=C_OK, ha='center',
              va='top')
    os.makedirs('results/figures', exist_ok=True)
    c.save('results/figures/vpr_pipeline_compact')


if __name__ == '__main__':
    main()
