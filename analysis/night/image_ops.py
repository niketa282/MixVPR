"""Image operations shared by the night analysis scripts (colour statistics and test-time interventions)."""
import numpy as np
from PIL import Image


def gray_world(img):
    """White balance: scale each colour channel so that its mean equals the overall mean (removes colour casts)."""
    a = np.asarray(img, dtype=np.float32)
    means = a.reshape(-1, 3).mean(axis=0)
    a = a * (means.mean() / np.maximum(means, 1e-6))
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def luminance_stretch(img, low=1, high=99):
    """Brightness/contrast normalisation without changing colour: stretch the luminance (Y) channel of YCbCr
    between its 1st and 99th percentiles, leaving the colour channels (Cb, Cr) untouched."""
    y, cb, cr = img.convert('YCbCr').split()
    a = np.asarray(y, dtype=np.float32)
    lo, hi = np.percentile(a, [low, high])
    a = (a - lo) / max(hi - lo, 1.0) * 255.0
    y = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    return Image.merge('YCbCr', (y, cb, cr)).convert('RGB')


def srgb_to_lab(a):
    """a: float array (..., 3) in [0, 255] sRGB -> CIE Lab (D65)."""
    c = a / 255.0
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    m = np.array([[0.4124564, 0.3575761, 0.1804375],
                  [0.2126729, 0.7151522, 0.0721750],
                  [0.0193339, 0.1191920, 0.9503041]])
    xyz = c @ m.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 216 / 24389, np.cbrt(xyz), (24389 / 27 * xyz + 16) / 116)
    L = 116 * f[..., 1] - 16
    A = 500 * (f[..., 0] - f[..., 1])
    B = 200 * (f[..., 1] - f[..., 2])
    return np.stack([L, A, B], axis=-1)
