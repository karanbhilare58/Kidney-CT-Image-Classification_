"""
Model service for loading PyTorch VGG16 model checkpoint and executing genuine inference.
Loads model artifacts once at application startup.
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import numpy as np
import torch
import torch.nn as nn
from torchvision import models
import joblib

from backend.app.preprocessing import (
    prepare_feature_frame,
    preprocess_image_bytes,
    DEFAULT_IMAGE_SIZE,
    DEFAULT_MEAN,
    DEFAULT_STD
)

logger = logging.getLogger("model_service")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

# Checkpoint candidate paths
CHECKPOINT_PATHS = [
    os.path.join(BASE_DIR, "models", "kidney_model.pth"),
    os.path.join(PROJECT_ROOT, "kidney_model.pth"),
    os.path.join(PROJECT_ROOT, "best_kidney_model.pth")
]

METADATA_PIPELINE_PATH = os.path.join(BASE_DIR, "models", "kidney_pipeline.joblib")
METADATA_PATH = os.path.join(BASE_DIR, "models", "model_metadata.json")


class ModelService:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.image_model: Optional[nn.Module] = None
        self.metadata_pipeline = None
        self.metadata: Dict[str, Any] = {}
        self.classes: List[str] = ["Cyst", "Normal", "Stone", "Tumor"]
        self.class_to_idx: Dict[str, int] = {c: i for i, c in enumerate(self.classes)}
        self.image_size: int = DEFAULT_IMAGE_SIZE
        self.mean: List[float] = DEFAULT_MEAN
        self.std: List[float] = DEFAULT_STD
        self.architecture: str = "vgg16"
        self.test_accuracy: float = 0.4219
        self.test_samples: int = 64
        self.is_image_model_loaded: bool = False
        self.is_metadata_pipeline_loaded: bool = False
        self.checkpoint_source: Optional[str] = None

    def load(self):
        """Loads both PyTorch model checkpoint and metadata pipeline once at startup."""
        logger.info(f"Initializing ModelService on device: {self.device}")

        # 1. Load PyTorch model checkpoint
        resolved_pth = None
        for p in CHECKPOINT_PATHS:
            if os.path.exists(p):
                resolved_pth = p
                break

        if resolved_pth:
            try:
                logger.info(f"Loading PyTorch model checkpoint from: {resolved_pth}")
                checkpoint = torch.load(resolved_pth, map_location=self.device)
                
                self.classes = checkpoint.get("class_names", self.classes)
                self.class_to_idx = checkpoint.get("class_to_idx", {c: i for i, c in enumerate(self.classes)})
                self.image_size = int(checkpoint.get("image_size", DEFAULT_IMAGE_SIZE))
                self.mean = checkpoint.get("mean", DEFAULT_MEAN)
                self.std = checkpoint.get("std", DEFAULT_STD)
                self.architecture = checkpoint.get("architecture", "vgg16")
                self.test_accuracy = float(checkpoint.get("test_accuracy", 0.4219))
                split_counts = checkpoint.get("split_counts", {})
                self.test_samples = int(split_counts.get("test", 64))

                # Instantiate model matching saved architecture
                if self.architecture.lower() == "vgg16":
                    model = models.vgg16(weights=None)
                    in_features = model.classifier[6].in_features
                    model.classifier[6] = nn.Linear(in_features, len(self.classes))
                else:
                    raise ValueError(f"Unsupported model architecture: {self.architecture}")

                model.load_state_dict(checkpoint["model_state_dict"])
                model.to(self.device)
                model.eval()

                self.image_model = model
                self.is_image_model_loaded = True
                self.checkpoint_source = resolved_pth
                logger.info(f"PyTorch {self.architecture.upper()} model loaded successfully ({len(self.classes)} classes).")
            except Exception as e:
                logger.error(f"Failed to load PyTorch model checkpoint from {resolved_pth}: {e}", exc_info=True)
                self.is_image_model_loaded = False
        else:
            logger.warning(f"No PyTorch model checkpoint found in searched paths: {CHECKPOINT_PATHS}")
            self.is_image_model_loaded = False

        # 2. Load dataset metadata search pipeline
        if os.path.exists(METADATA_PIPELINE_PATH):
            try:
                logger.info(f"Loading metadata search pipeline from {METADATA_PIPELINE_PATH}...")
                self.metadata_pipeline = joblib.load(METADATA_PIPELINE_PATH)
                self.is_metadata_pipeline_loaded = True
                logger.info("Metadata search pipeline loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load metadata pipeline: {e}")
                self.is_metadata_pipeline_loaded = False
        else:
            logger.warning(f"Metadata pipeline artifact not found at {METADATA_PIPELINE_PATH}")
            self.is_metadata_pipeline_loaded = False

        # 3. Load optional model metadata file
        if os.path.exists(METADATA_PATH):
            try:
                with open(METADATA_PATH, "r") as f:
                    self.metadata = json.load(f)
            except Exception as e:
                logger.warning(f"Could not read metadata file: {e}")

    @property
    def is_loaded(self) -> bool:
        """Returns True if either the image model or metadata pipeline is loaded."""
        return self.is_image_model_loaded or self.is_metadata_pipeline_loaded

    def predict_image(self, image_bytes: bytes, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes genuine visual feature classification on an uploaded CT scan image
        using the PyTorch VGG16 model.
        """
        if not self.is_image_model_loaded or self.image_model is None:
            raise RuntimeError("PyTorch model checkpoint is missing or not loaded.")

        # 1. Preprocess and validate image into normalized tensor
        tensor = preprocess_image_bytes(
            image_bytes=image_bytes,
            image_size=self.image_size,
            mean=self.mean,
            std=self.std
        ).to(self.device)

        # 2. PyTorch model inference
        with torch.no_grad():
            logits = self.image_model(tensor)
            probs = torch.softmax(logits, dim=1)[0].cpu().numpy()

        pred_idx = int(np.argmax(probs))
        prediction = self.classes[pred_idx]
        confidence = float(round(float(probs[pred_idx]), 4))

        # 3. Format class probabilities distribution
        class_probabilities = {
            self.classes[i]: float(round(float(probs[i]), 4))
            for i in range(len(self.classes))
        }

        # 4. Genuine visual summary metrics for frontend transparency
        mean_intensity = float(round(float(tensor.mean().item()), 4))

        return {
            "prediction": prediction,
            "confidence": confidence,
            "confidence_percentage": f"{confidence * 100:.2f}%",
            "class_probabilities": class_probabilities,
            "features_used": {
                "image_dimensions": [3, self.image_size, self.image_size],
                "filename": filename or "uploaded_scan",
                "mean_intensity": mean_intensity,
                "architecture": self.architecture,
                "device": str(self.device),
                "model_status": "PyTorch VGG16 development checkpoint"
            },
            "inference_mode": "pytorch_vgg16_visual_analysis",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def predict_features(self, image_id: Optional[str] = None, path: Optional[str] = None) -> Dict[str, Any]:
        """Executes metadata search/prediction on dataset identifiers."""
        if not self.is_metadata_pipeline_loaded or self.metadata_pipeline is None:
            raise RuntimeError("Dataset metadata search pipeline is not loaded or available.")

        feature_df = prepare_feature_frame(image_id=image_id, path=path)
        prediction = str(self.metadata_pipeline.predict(feature_df)[0])

        probabilities = {}
        if hasattr(self.metadata_pipeline, "predict_proba"):
            probs = self.metadata_pipeline.predict_proba(feature_df)[0]
            pipe_classes = list(self.metadata_pipeline.classes_)
            for cls_name, p in zip(pipe_classes, probs):
                probabilities[str(cls_name)] = float(round(p, 4))
            confidence = float(probabilities.get(prediction, max(probs)))
        else:
            confidence = 1.0
            probabilities = {cls: (1.0 if cls == prediction else 0.0) for cls in self.classes}

        return {
            "prediction": prediction,
            "confidence": round(confidence, 4),
            "confidence_percentage": f"{confidence * 100:.2f}%",
            "class_probabilities": probabilities,
            "features_used": {
                "image_id": feature_df["image_id"].iloc[0],
                "path": feature_df["path"].iloc[0]
            },
            "inference_mode": "dataset_metadata_index",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Global model service instance
model_service = ModelService()
