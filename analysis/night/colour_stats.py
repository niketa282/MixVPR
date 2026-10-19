"""Colour statistics of the SVOX query sets vs. the (daytime) SVOX database. CPU only.

For a random sample of images per set it measures:
  L*      mean lightness (0 = black, 100 = white)
  a*, b*  mean colour cast (a*: + red / - green, b*: + yellow / - blue); 0 = neutral grey
  cast    distance of the mean colour from neutral grey, sqrt(a*^2 + b*^2)
  sat     mean HSV saturation (0-1)
  contrast  standard deviation of L* within an image

Usage (from the repo root):
    python analysis/night/colour_stats.py --n 400
"""
import argparse
import glob
import os
import random
import sys

import numpy as np
import pandas as pd
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from image_ops import srgb_to_lab  # noqa: E402

ROOT = '/iridisfs/geosets/svox/images/test'
SETS = ['gallery', 'queries_overcast', 'queries_sun', 'queries_rain', 'queries_snow', 'queries_night']
NAMES = {'gallery': 'Database (day)', 'queries_overcast': 'Overcast', 'queries_sun': 'Sun', 'queries_rain': 'Rain',
         'queries_snow': 'Snow', 'queries_night': 'Night'}


def stats(path):
    img = Image.open(path).convert('RGB').resize((320, 320))
    a = np.asarray(img, dtype=np.float32)
    lab = srgb_to_lab(a)
    hsv = np.asarray(img.convert('HSV'), dtype=np.float32) / 255.0
    L, A, B = lab[..., 0], lab[..., 1], lab[..., 2]
    return dict(L=L.mean(), a=A.mean(), b=B.mean(), cast=float(np.hypot(A.mean(), B.mean())),
                sat=hsv[..., 1].mean(), contrast=L.std())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--n', type=int, default=400, help='images sampled per set')
    ap.add_argument('--out', default='results/night_analysis')
    args = ap.parse_args()
    random.seed(0)
    rows = []
    for s in SETS:
        paths = sorted(glob.glob(os.path.join(ROOT, s, '*.jpg')))
        for p in random.sample(paths, min(args.n, len(paths))):
            rows.append(dict(set=NAMES[s], **stats(p)))
    df = pd.DataFrame(rows)
    os.makedirs(args.out, exist_ok=True)
    df.to_csv(os.path.join(args.out, 'colour_stats_per_image.csv'), index=False)
    summary = df.groupby('set', sort=False).agg(['mean', 'std']).round(2)
    summary.to_csv(os.path.join(args.out, 'colour_stats_summary.csv'))
    pd.set_option('display.width', 200)
    print(df.groupby('set', sort=False).mean().round(2).to_string())


if __name__ == '__main__':
    main()
