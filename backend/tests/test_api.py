"""
Comprehensive test suite for Kidney CT Image Condition Classification API.
Audits health, metadata, PyTorch visual inference, base64 uploads,
invalid inputs, corrupted image bytes, unsupported formats, and missing checkpoint handling.
"""

import os
import io
import base64
import pytest
from PIL import Image
from fastapi.testclient import TestClient
import torch

from backend.app.main import app
from backend.app.model_service import model_service
from backend.app.preprocessing import preprocess_image_bytes

client = TestClient(app)

SAMPLE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "sample_images"
)


@pytest.fixture(scope="module", autouse=True)
def setup_models():
    """Ensure PyTorch model and metadata pipeline are loaded for all tests."""
    model_service.load()
    assert model_service.is_image_model_loaded, "PyTorch image model should be loaded."
    assert model_service.is_metadata_pipeline_loaded, "Metadata pipeline should be loaded."


def test_model_service_pytorch_loading():
    """Verify PyTorch model architecture, device, and class ordering."""
    assert model_service.image_model is not None
    assert model_service.architecture == "vgg16"
    assert model_service.image_size == 224
    assert model_service.classes == ["Cyst", "Normal", "Stone", "Tumor"]
    assert len(model_service.mean) == 3
    assert len(model_service.std) == 3


def test_image_preprocessing_pipeline():
    """Verify image preprocessing produces the expected (1, 3, 224, 224) PyTorch tensor."""
    img = Image.new("RGB", (300, 300), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    tensor = preprocess_image_bytes(buf.getvalue(), image_size=224)
    assert isinstance(tensor, torch.Tensor)
    assert tensor.shape == (1, 3, 224, 224)
    assert tensor.dtype == torch.float32


def test_prediction_output_shape_and_labels():
    """Verify PyTorch forward pass outputs shape (1, 4) and valid class probability distribution."""
    assert model_service.image_model is not None
    dummy_input = torch.randn(1, 3, 224, 224).to(model_service.device)
    with torch.no_grad():
        logits = model_service.image_model(dummy_input)
    assert logits.shape == (1, 4)
    probs = torch.softmax(logits, dim=1)[0].cpu().numpy()
    assert len(probs) == 4
    assert float(probs.sum()) == pytest.approx(1.0, abs=0.001)
    for p in probs:
        assert 0.0 <= p <= 1.0


def test_root_endpoint():
    """Verify API metadata, title, and terminology."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "Kidney CT" in data["title"]
    assert set(data["supported_classes"]) == {"Normal", "Cyst", "Stone", "Tumor"}
    assert "endpoints" in data


def test_health_endpoint():
    """Verify health status, loaded PyTorch model, metrics, and development disclaimer."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True
    assert data["image_model_loaded"] is True
    assert data["metadata_pipeline_loaded"] is True
    assert "PyTorch" in data["model_type"]
    assert "VGG16" in data["model_type"]
    assert data["evaluation_accuracy"] is not None
    assert 0.0 <= data["evaluation_accuracy"] <= 1.0
    assert data["disclaimer"] is not None
    assert "development checkpoint" in data["disclaimer"].lower()


def test_features_endpoint():
    """Verify feature metadata schema and sample inputs."""
    response = client.get("/features")
    assert response.status_code == 200
    data = response.json()
    assert data["target"] == "diag"
    assert set(data["target_classes"]) == {"Normal", "Cyst", "Stone", "Tumor"}
    feature_names = [f["name"] for f in data["features"]]
    assert "image_file" in feature_names
    assert "image_id" in feature_names
    assert len(data["sample_inputs"]) == 4


def test_samples_endpoint():
    """Verify representative samples from kidneyData.csv."""
    response = client.get("/samples")
    assert response.status_code == 200
    samples = response.json()
    assert len(samples) == 4
    diagnoses = {s["diag"] for s in samples}
    assert diagnoses == {"Normal", "Cyst", "Stone", "Tumor"}


def _get_test_image_bytes(filename: str, color_intensity: int = 128) -> bytes:
    """Returns local sample image bytes if present; otherwise creates synthetic test image."""
    path = os.path.join(SAMPLE_DIR, filename)
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f.read()
    img = Image.new("RGB", (224, 224), color=(color_intensity, color_intensity, color_intensity))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_valid_image_inference_normal():
    """Verify PyTorch model inference on normal_sample.jpg or synthetic normal scan."""
    raw_bytes = _get_test_image_bytes("normal_sample.jpg", 100)
    files = {"file": ("normal_scan.jpg", raw_bytes, "image/jpeg")}
    response = client.post("/predict/image", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["prediction"] in ["Normal", "Cyst", "Stone", "Tumor"]
    assert data["inference_mode"] == "pytorch_vgg16_visual_analysis"
    assert 0.0 <= data["confidence"] <= 1.0
    probs = data["class_probabilities"]
    assert len(probs) == 4
    assert sum(probs.values()) == pytest.approx(1.0, abs=0.01)
    assert data["features_used"]["architecture"] == "vgg16"
    assert "mean_intensity" in data["features_used"]
    assert data["features_used"]["image_dimensions"] == [3, 224, 224]


def test_valid_image_inference_cyst():
    """Verify PyTorch model inference on cyst_sample.jpg or synthetic cyst scan."""
    raw_bytes = _get_test_image_bytes("cyst_sample.jpg", 60)
    files = {"file": ("cyst_scan.jpg", raw_bytes, "image/jpeg")}
    response = client.post("/predict/image", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["prediction"] in ["Normal", "Cyst", "Stone", "Tumor"]
    assert 0.0 <= data["confidence"] <= 1.0


def test_valid_image_inference_stone():
    """Verify PyTorch model inference on stone_crop.jpg or synthetic stone scan."""
    raw_bytes = _get_test_image_bytes("stone_crop.jpg", 210)
    files = {"file": ("stone_scan.jpg", raw_bytes, "image/jpeg")}
    response = client.post("/predict/image", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["prediction"] in ["Normal", "Cyst", "Stone", "Tumor"]
    assert 0.0 <= data["confidence"] <= 1.0


def test_valid_image_inference_tumor():
    """Verify PyTorch model inference on tumor_crop.jpg or synthetic tumor scan."""
    raw_bytes = _get_test_image_bytes("tumor_crop.jpg", 160)
    files = {"file": ("tumor_scan.jpg", raw_bytes, "image/jpeg")}
    response = client.post("/predict/image", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["prediction"] in ["Normal", "Cyst", "Stone", "Tumor"]
    assert 0.0 <= data["confidence"] <= 1.0


def test_valid_base64_inference():
    """Verify base64 image inference via POST /predict."""
    raw_bytes = _get_test_image_bytes("normal_sample.jpg", 100)
    raw_b64 = base64.b64encode(raw_bytes).decode("utf-8")
    payload = {"image_base64": f"data:image/jpeg;base64,{raw_b64}"}
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["prediction"] in ["Normal", "Cyst", "Stone", "Tumor"]
    assert data["inference_mode"] == "pytorch_vgg16_visual_analysis"
    assert 0.0 <= data["confidence"] <= 1.0


def test_invalid_empty_file_upload():
    """Rejects empty 0-byte file with 400 Bad Request."""
    files = {"file": ("empty.jpg", b"", "image/jpeg")}
    response = client.post("/predict/image", files=files)
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_unsupported_file_type_text():
    """Rejects non-image file formats with 400 Bad Request."""
    files = {"file": ("notes.txt", b"medical report text", "text/plain")}
    response = client.post("/predict/image", files=files)
    assert response.status_code == 400
    assert "unsupported" in response.json()["detail"].lower()


def test_corrupted_image_file():
    """Rejects corrupted / fake image bytes with 400 Bad Request."""
    files = {"file": ("corrupted.jpg", b"NOT_A_REAL_JPEG_IMAGE_HEADER_123456789", "image/jpeg")}
    response = client.post("/predict/image", files=files)
    assert response.status_code == 400
    assert "corrupted" in response.json()["detail"].lower() or "invalid" in response.json()["detail"].lower()


def test_predict_metadata_valid():
    """Verify dataset metadata search via POST /predict."""
    payload = {
        "image_id": "Normal- (849)",
        "path": "CT-KIDNEY-DATASET-Normal-Cyst-Tumor-Stone/Normal/Normal- (849).jpg"
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["prediction"] == "Normal"
    assert data["inference_mode"] == "dataset_metadata_index"


def test_predict_invalid_empty_payload():
    """Rejects empty JSON payload with 422 Unprocessable Entity."""
    response = client.post("/predict", json={})
    assert response.status_code == 422


def test_missing_model_graceful_handling():
    """Verifies 503 response when image model is unavailable."""
    original_flag = model_service.is_image_model_loaded
    model_service.is_image_model_loaded = False
    try:
        img_path = os.path.join(SAMPLE_DIR, "normal_sample.jpg")
        with open(img_path, "rb") as f:
            files = {"file": ("normal_scan.jpg", f, "image/jpeg")}
            response = client.post("/predict/image", files=files)
        assert response.status_code == 503
        assert "unavailable" in response.json()["detail"].lower()
    finally:
        model_service.is_image_model_loaded = original_flag
