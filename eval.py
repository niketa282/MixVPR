"""Evaluate the best checkpoint of each training condition on the test sets.

Test sets are in the VPR-datasets-downloader format: image names start with
@UTM_east@UTM_north@, and a database image is a positive for a query if it lies
within 25 m (for Nordland, the coordinates are frame indices scaled so that 25
corresponds to +/-10 frames).

Usage:
    python eval.py                                   # all conditions, all test sets
    python eval.py --conditions none rotate --datasets pitts30k_test nordland
"""
import argparse
import csv
import glob
import os
import re
from os.path import join

import numpy as np
import torch
import torchvision.transforms as T
from PIL import Image
from sklearn.neighbors import NearestNeighbors
from torch.utils.data import DataLoader, Dataset

import utils
from main import VPRModel

GEOSETS = '/iridisfs/geosets'

# name: (database folder, queries folder)
TEST_SETS = {
    'pitts30k_test':  ('pitts30k/images/test/database', 'pitts30k/images/test/queries'),
    'nordland':       ('nordland/images/test/database', 'nordland/images/test/queries'),
    'svox':           ('svox/images/test/gallery',      'svox/images/test/queries'),
    'svox_night':     ('svox/images/test/gallery',      'svox/images/test/queries_night'),
    'svox_overcast':  ('svox/images/test/gallery',      'svox/images/test/queries_overcast'),
    'svox_rain':      ('svox/images/test/gallery',      'svox/images/test/queries_rain'),
    'svox_snow':      ('svox/images/test/gallery',      'svox/images/test/queries_snow'),
    'svox_sun':       ('svox/images/test/gallery',      'svox/images/test/queries_sun'),
    'pitts250k_test': ('pitts250k/images/test/database', 'pitts250k/images/test/queries'),
    'msls_val':       ('msls/val/database',             'msls/val/queries'),
    'tokyo247':       ('tokyo247/images/test/database', 'tokyo247/images/test/queries'),
    'sf_xl_small':    ('small/test/database',           'small/test/queries_v1'),
    'amstertime':     ('amstertime/images/test/database', 'amstertime/images/test/queries'),  # 1-to-1 pairs, 1000 m apart
    'st_lucia':       ('st_lucia/images/test/database', 'st_lucia/images/test/queries'),
    'eynsham':        ('eynsham/images/test/database',  'eynsham/images/test/queries'),
}

CONDITIONS = ['none', 'crop', 'perspective', 'rotate', 'translate', 'shear']

POS_DIST_THRESHOLD = 25  # metres (frames x 2.4 for Nordland)
K_VALUES = [1, 5, 10, 15, 20, 50, 100]

# same as the validation transform used during training
EVAL_TRANSFORM = T.Compose([
    T.Resize((320, 320), interpolation=T.InterpolationMode.BILINEAR),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


class TestDataset(Dataset):
    """Database images followed by query images, like PittsburgDataset during validation."""

    def __init__(self, db_dir, q_dir, transform=EVAL_TRANSFORM):
        self.db_paths = sorted(glob.glob(join(db_dir, '**', '*.jpg'), recursive=True))
        self.q_paths = sorted(glob.glob(join(q_dir, '**', '*.jpg'), recursive=True))
        if not self.db_paths or not self.q_paths:
            raise FileNotFoundError(f'No images found in {db_dir} or {q_dir}')
        self.images = self.db_paths + self.q_paths
        self.num_references = len(self.db_paths)
        self.transform = transform

    @staticmethod
    def utm(paths):
        # @UTM_east@UTM_north@...jpg
        return np.array([(float(os.path.basename(p).split('@')[1]),
                          float(os.path.basename(p).split('@')[2])) for p in paths])

    def get_positives(self):
        knn = NearestNeighbors(n_jobs=-1)
        knn.fit(self.utm(self.db_paths))
        return knn.radius_neighbors(self.utm(self.q_paths), radius=POS_DIST_THRESHOLD,
                                    return_distance=False)

    def __getitem__(self, index):
        img = Image.open(self.images[index]).convert('RGB')
        return self.transform(img), index

    def __len__(self):
        return len(self.images)


def best_checkpoint(condition, seed, logs_dir='./LOGS'):
    """Highest R1 in the filename; ties go to the later epoch."""
    ckpts = glob.glob(join(logs_dir, f'rgb_{condition}_s{seed}', 'lightning_logs', '*', 'checkpoints', '*.ckpt'))
    if not ckpts:
        raise FileNotFoundError(f'No checkpoints found for condition {condition}, seed {seed}')

    def key(path):
        r1 = float(re.search(r'R1\[([\d.]+)\]', path).group(1))
        epoch = int(re.search(r'epoch\((\d+)\)', path).group(1))
        return (r1, epoch)

    return max(ckpts, key=key)


@torch.no_grad()
def compute_descriptors(model, dataset, batch_size, num_workers):
    loader = DataLoader(dataset, batch_size=batch_size, num_workers=num_workers,
                        shuffle=False, pin_memory=True)
    descriptors = []
    for images, _ in loader:
        # fp16 autocast, as in training/validation (precision=16)
        with torch.autocast('cuda', dtype=torch.float16):
            descriptors.append(model(images.cuda(non_blocking=True)).float().cpu())
    return torch.cat(descriptors, dim=0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--conditions', nargs='+', default=CONDITIONS)
    parser.add_argument('--datasets', nargs='+', default=list(TEST_SETS), choices=list(TEST_SETS))
    parser.add_argument('--batch_size', type=int, default=120)
    parser.add_argument('--num_workers', type=int, default=8)
    parser.add_argument('--out', default=None)
    parser.add_argument('--seed', type=int, default=190223)
    args = parser.parse_args()
    if args.out is None:
        args.out = f'results/seed{args.seed}/test_results.csv'

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    write_header = not os.path.exists(args.out)

    with open(args.out, 'a', newline='') as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(['seed','condition', 'dataset', 'R1', 'R5', 'R10', 'num_db', 'num_queries', 'checkpoint'])

        for condition in args.conditions:
            ckpt = best_checkpoint(condition, args.seed)
            print(f'\n===== {condition}: {ckpt}')
            model = VPRModel.load_from_checkpoint(ckpt, map_location='cpu').cuda().eval()

            for name in args.datasets:
                db_dir, q_dir = (join(GEOSETS, d) for d in TEST_SETS[name])
                dataset = TestDataset(db_dir, q_dir)
                feats = compute_descriptors(model, dataset, args.batch_size, args.num_workers)

                recalls = utils.get_validation_recalls(
                    r_list=feats[:dataset.num_references],
                    q_list=feats[dataset.num_references:],
                    k_values=K_VALUES,
                    gt=dataset.get_positives(),
                    print_results=True,
                    dataset_name=f'{name} ({condition})',
                    faiss_gpu=False,
                )
                writer.writerow([args.seed, condition, name,
                                 f'{100 * recalls[1]:.2f}', f'{100 * recalls[5]:.2f}', f'{100 * recalls[10]:.2f}',
                                 dataset.num_references, len(dataset) - dataset.num_references, ckpt])
                f.flush()

            del model
            torch.cuda.empty_cache()


if __name__ == '__main__':
    main()
