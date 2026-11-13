"""CPU cost per image of each augmentation policy, measured on the same machine.

Isolates the augmentation step from node-to-node variation in training time.

    python results/time_augmentations.py
"""
import glob
import os
import random
import sys
import time
import numpy as np
import torch
from PIL import Image
from torchvision import transforms as T

# the script lives in results/, but dataloaders/ is in the repo root: add the root to the import search path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dataloaders.GSVCitiesDataloader import IMAGENET_MEAN_STD, TrivialAugmentBounded

N = 3000          # number of images timed per policy
SEED = 190223     # same seed as the main experiments
IMAGE_SIZE = (320, 320)
BASE_PATH = '/iridisfs/geosets/gsvcities/'
IMAGE_PATH = sorted(glob.glob(BASE_PATH + 'Images/London/*.jpg'))[0]

random.seed(SEED)          # TrivialAugmentBounded picks its magnitude with random
torch.manual_seed(SEED)    # RandAugment / TrivialAugment pick their operations with torch
torch.set_num_threads(1)   # one thread, like a single data-loading worker; keeps timings stable

img = Image.open(IMAGE_PATH).convert('RGB')
transform = T.Resize(IMAGE_SIZE, interpolation=T.InterpolationMode.BILINEAR)
img = transform(img)

POLICIES = {
            'none': lambda x: x,
            'randaugment': T.RandAugment(num_ops=3, interpolation=T.InterpolationMode.BILINEAR),
            'randaugment_1op': T.RandAugment(num_ops=1, interpolation=T.InterpolationMode.BILINEAR),
            'trivialaugment': T.TrivialAugmentWide(interpolation=T.InterpolationMode.BILINEAR),
            'trivialaugment_bounded': TrivialAugmentBounded(maximum_strength=18),
}

POST = T.Compose([T.ToTensor(), T.Normalize(IMAGENET_MEAN_STD['mean'], IMAGENET_MEAN_STD['std'])])

for name, transform in POLICIES.items():
    # 1. warm up: run 50 times without timing
    for _ in range(50):
        POST(transform(img))
    
    # 2. start the stopwatch
    start = time.perf_counter()
    # 3. run N times
    for _ in range(N):
        POST(transform(img))
    # 4. stop the stopwatch and work out how long it took
    stop = time.perf_counter()
    elapsed = stop - start
    # 5. turn that into milliseconds per image
    ms = (elapsed/N) * 1000
    # 6. print the name and the result
    print(f'{name:24s} {ms:.2f} ms/image')