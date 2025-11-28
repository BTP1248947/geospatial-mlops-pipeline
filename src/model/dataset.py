# src/model/dataset.py
import pandas as pd
import numpy as np
from PIL import Image
from torch.utils.data import Dataset
import torch

class LEVIRChangeDataset(Dataset):
    """
    Expects mapping CSV with columns: before,after,mask
    Returns x: float32 tensor (6,H,W) in [0,1], y: float32 tensor (1,H,W) {0,1}
    """
    def __init__(self, mapping_csv, transforms=None):
        self.df = pd.read_csv(mapping_csv)
        self.df = self.df.astype(str)  # ensure safe paths
        self.transforms = transforms

    def __len__(self):
        return len(self.df)

    def _load_rgb(self, path):
        img = Image.open(path).convert("RGB")
        return np.array(img, dtype=np.uint8)

    def _load_mask(self, path):
        m = Image.open(path).convert("L")
        return np.array(m, dtype=np.uint8)

    # inside src/model/dataset.py: replace __getitem__ with this
    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        # try keyed access, else positional
        try:
            before_p = row['before']
            after_p  = row['after']
            mask_p   = row['mask']
        except Exception:
            # fallback: assume first three columns are before, after, mask
            vals = row.values
            if len(vals) < 3:
                raise RuntimeError("Mapping CSV row has fewer than 3 columns.")
            before_p, after_p, mask_p = vals[0], vals[1], vals[2]

        before = self._load_rgb(before_p)
        after  = self._load_rgb(after_p)
        mask   = self._load_mask(mask_p)

        x = np.concatenate([before, after], axis=2).astype('float32') / 255.0
        x = np.transpose(x, (2,0,1))
        y = (mask > 127).astype('float32')[None, ...]

        return torch.from_numpy(x), torch.from_numpy(y)

