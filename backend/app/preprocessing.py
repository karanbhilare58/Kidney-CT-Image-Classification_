"""
Preprocessing utilities for Kidney CT Image Condition Classification.
Ensures strict feature ordering, input validation, image normalization,
and PyTorch tensor transformation matching training.
"""

import base64
import io
import re
from typing import Optional, Tuple, List, Union
import numpy as np
import pandas as pd
from PIL import Image
import torch
from torchvision import transforms

FEATURE_COLUMNS = ["image_id", "path"]
DEFAULT_IMAGE_SIZE = 224
DEFAULT_MEAN = [0.485, 0.456, 0.406]
DEFAULT_STD = [0.229, 0.224, 0.225]


def sanitize_text(val: Optional[str]) -> str:
    """Sanitizes text inputs by stripping whitespace and removing null bytes."""
    if val is None:
        return ""
    s = str(val).strip()
    return re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", s)


def prepare_feature_frame(image_id: Optional[str] = None, path: Optional[str] = None) -> pd.DataFrame:
    """
    Constructs a 1-row DataFrame preserving the exact feature ordering
    expected by the metadata pipeline: ['image_id', 'path'].
    """
    cleaned_id = sanitize_text(image_id)
    cleaned_path = sanitize_text(path)

    data = {
        "image_id": [cleaned_id],
        "path": [cleaned_path]
    }
    df = pd.DataFrame(data)
    return df[FEATURE_COLUMNS]


def decode_base64_image(b64_str: str) -> bytes:
    """Decodes a base64-encoded image string, handling data URI prefixes."""
    clean_b64 = b64_str.strip()
    if "," in clean_b64 and "base64" in clean_b64:
        clean_b64 = clean_b64.split(",", 1)[1]

    try:
        raw_bytes = base64.b64decode(clean_b64, validate=True)
        if len(raw_bytes) == 0:
            raise ValueError("Decoded image data is empty (0 bytes).")
        return raw_bytes
    except Exception as e:
        raise ValueError(f"Invalid or corrupted base64 image data: {str(e)}")


def get_inference_transform(
    image_size: int = DEFAULT_IMAGE_SIZE,
    mean: List[float] = DEFAULT_MEAN,
    std: List[float] = DEFAULT_STD
) -> transforms.Compose:
    """Returns the torchvision transform matching the model training evaluation pipeline."""
    return transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=mean, std=std)
    ])


def preprocess_image_bytes(
    image_bytes: bytes,
    image_size: int = DEFAULT_IMAGE_SIZE,
    mean: List[float] = DEFAULT_MEAN,
    std: List[float] = DEFAULT_STD
) -> torch.Tensor:
    """
    Preprocesses raw image bytes into a normalized PyTorch tensor (1, 3, image_size, image_size).
    Strictly validates file integrity and rejects corrupted, truncated, or empty files.
    """
    if not image_bytes or len(image_bytes) == 0:
        raise ValueError("Image file is empty (0 bytes).")

    try:
        # Step 1: verify file structure
        with Image.open(io.BytesIO(image_bytes)) as img:
            img.verify()
    except Exception as e:
        raise ValueError(f"Corrupted or invalid image file: {str(e)}")

    try:
        # Step 2: load, convert to RGB, and apply torchvision transform
        with Image.open(io.BytesIO(image_bytes)) as img:
            img_rgb = img.convert("RGB")
            transform = get_inference_transform(image_size=image_size, mean=mean, std=std)
            tensor = transform(img_rgb)
            return tensor.unsqueeze(0)  # Shape: (1, 3, image_size, image_size)
    except Exception as e:
        raise ValueError(f"Failed to process image: {str(e)}")
