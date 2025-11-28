# src/model/model.py
import torch
import torch.nn as nn
import segmentation_models_pytorch as smp

def _find_first_conv_key(state_dict, in_ch):
    for k, v in state_dict.items():
        if v.ndim == 4 and v.shape[1] == in_ch and v.shape[2] in (3,7,5):
            return k
    return None

def build_unet_in6(encoder_name="resnet34", encoder_weights="imagenet", classes=1, activation=None, device="cpu"):
    """
    Build a Unet with in_channels=6. If encoder_weights == "imagenet",
    create a 3-channel reference model with Imagenet weights and transfer weights
    into a 6-channel model by copying pretrained filters into both halves.
    """
    device = torch.device(device)
    # target model with 6-channel input (no encoder weights initially)
    model6 = smp.Unet(
        encoder_name=encoder_name,
        encoder_weights=None,
        in_channels=6,
        classes=classes,
        activation=activation,
    )

    if not encoder_weights:
        return model6.to(device)

    # reference model with 3-channel Imagenet weights
    model3 = smp.Unet(
        encoder_name=encoder_name,
        encoder_weights=encoder_weights,
        in_channels=3,
        classes=classes,
        activation=activation,
    )

    sd3 = model3.state_dict()
    sd6 = model6.state_dict()

    k3 = _find_first_conv_key(sd3, in_ch=3)
    k6 = _find_first_conv_key(sd6, in_ch=6)
    if k3 is None or k6 is None:
        raise RuntimeError("Could not find first conv key in state dicts for encoder")

    w3 = sd3[k3]  # shape (out, 3, kh, kw)
    out_ch, in3, kh, kw = w3.shape
    if in3 != 3:
        raise RuntimeError("Unexpected pretrained first conv in_channels != 3")

    # create 6-channel weight by copying the 3-channel filters into both halves
    w6 = torch.zeros((out_ch, 6, kh, kw), dtype=w3.dtype)
    w6[:, :3, :, :] = w3
    w6[:, 3:, :, :] = w3.clone()

    sd6[k6] = w6

    # copy rest of matching keys from sd3 to sd6
    for k, v in sd3.items():
        if k == k3:
            continue
        if k in sd6 and sd6[k].shape == v.shape:
            sd6[k] = v

    model6.load_state_dict(sd6)
    return model6.to(device)
