"""Test-time interventions: evaluate existing (unchanged) models with modified test images.

Changes only the images given to already-trained models, to find out what makes night images hard:
  none         standard evaluation (reference)
  grayworld_q  white-balance the queries only (removes colour casts; database unchanged)
  lumstretch_q stretch brightness/contrast of the queries only, colours unchanged
  both_q       white balance + brightness/contrast stretch on the queries
  gray_both    convert queries and database to grayscale (removes colour entirely; RGB models only)

Reuses eval.py's checkpoint lookup, ground truth and recall code without modifying eval.py.
Database descriptors are computed once per model and transform and shared across query sets.

Usage (GPU, via analysis/night/night.slurm):
    python analysis/night/test_time.py --input rgb --conditions none
"""
import argparse
import csv
import os
import sys

import torch
import torchvision.transforms as T
from PIL import Image
from torch.utils.data import Dataset

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.getcwd())
import utils  # noqa: E402
from eval import GEOSETS, K_VALUES, TEST_SETS, TestDataset, best_checkpoint, compute_descriptors  # noqa: E402
from main import VPRModel  # noqa: E402
from image_ops import gray_world, luminance_stretch  # noqa: E402

NORM = [T.ToTensor(), T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])]
RESIZE = T.Resize((320, 320), interpolation=T.InterpolationMode.BILINEAR)


def make(pre=None, gray=False):
    ops = [RESIZE] + ([T.Lambda(pre)] if pre else []) + ([T.Grayscale(num_output_channels=3)] if gray else [])
    return T.Compose(ops + NORM)


class ImageList(Dataset):
    def __init__(self, paths, transform):
        self.paths, self.transform = paths, transform

    def __getitem__(self, i):
        return self.transform(Image.open(self.paths[i]).convert('RGB')), i

    def __len__(self):
        return len(self.paths)


def interventions(input_type):
    """name -> (database transform key, query transform)."""
    gray = input_type == 'gray'
    out = {'none': ('base', make(gray=gray)),
           'grayworld_q': ('base', make(gray_world, gray)),
           'lumstretch_q': ('base', make(luminance_stretch, gray)),
           'both_q': ('base', make(lambda im: luminance_stretch(gray_world(im)), gray))}
    if not gray:
        out['gray_both'] = ('gray', make(gray=True))
    db_tfs = {'base': make(gray=gray), 'gray': make(gray=True)}
    return out, db_tfs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', default='rgb', choices=['rgb', 'gray'])
    ap.add_argument('--conditions', nargs='+', default=['none'])
    ap.add_argument('--seeds', type=int, nargs='+', default=[190223, 1, 2])
    ap.add_argument('--datasets', nargs='+', default=['svox_night', 'svox_overcast', 'svox_sun'])
    ap.add_argument('--out', default='results/night_analysis/test_time_interventions.csv')
    ap.add_argument('--batch_size', type=int, default=120)
    ap.add_argument('--num_workers', type=int, default=8)
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    new = not os.path.exists(args.out)
    ivs, db_tfs = interventions(args.input)
    with open(args.out, 'a', newline='') as f:
        w = csv.writer(f)
        if new:
            w.writerow(['input', 'condition', 'seed', 'dataset', 'intervention', 'R1', 'R5', 'R10'])
        for cond in args.conditions:
            for seed in args.seeds:
                ckpt = best_checkpoint(cond, seed, args.input)
                model = VPRModel.load_from_checkpoint(ckpt, map_location='cpu').cuda().eval()
                db_cache = {}
                for ds in args.datasets:
                    db_dir, q_dir = (os.path.join(GEOSETS, d) for d in TEST_SETS[ds])
                    split = TestDataset(db_dir, q_dir)  # only for the file lists and ground truth
                    gt = split.get_positives()
                    for name, (db_key, q_tf) in ivs.items():
                        if (db_dir, db_key) not in db_cache:
                            db_cache[(db_dir, db_key)] = compute_descriptors(
                                model, ImageList(split.db_paths, db_tfs[db_key]), args.batch_size, args.num_workers)
                        q = compute_descriptors(model, ImageList(split.q_paths, q_tf), args.batch_size,
                                                args.num_workers)
                        rec = utils.get_validation_recalls(
                            r_list=db_cache[(db_dir, db_key)], q_list=q, k_values=K_VALUES, gt=gt,
                            print_results=False, faiss_gpu=False, dataset_name=f'{ds} {name}')
                        w.writerow([args.input, cond, seed, ds, name] + [f'{100 * rec[k]:.2f}' for k in (1, 5, 10)])
                        f.flush()
                        print(f'{args.input} {cond} s{seed} {ds:14s} {name:12s} R@1 {100 * rec[1]:.2f}', flush=True)
                del model
                torch.cuda.empty_cache()


if __name__ == '__main__':
    main()
