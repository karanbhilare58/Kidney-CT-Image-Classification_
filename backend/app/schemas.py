"""
Pydantic schemas for the Chronic Kidney Disease Analysis API.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, model_validator


class FeatureItem(BaseModel):
    name: str = Field(..., description="Feature name")
    type: str = Field(..., description="Data type (e.g., string, float)")
    description: str = Field(..., description="Human-readable feature description")
    required: bool = Field(..., description="Whether this feature is mandatory")
    example: Any = Field(..., description="Example value")
    constraints: Optional[Dict[str, Any]] = Field(default=None, description="Validation constraints")


class FeaturesResponse(BaseModel):
    target: str = Field(..., description="Target prediction variable name")
    target_classes: List[str] = Field(..., description="List of possible diagnostic classes")
    features: List[FeatureItem] = Field(..., description="List of supported input features")
    sample_inputs: List[Dict[str, Any]] = Field(..., description="Verified sample inputs from dataset")


class PredictionRequest(BaseModel):
    image_id: Optional[str] = Field(
        default=None,
        max_length=250,
        description="Kidney scan image ID, e.g. 'Normal- (849)' or 'Tumor- (1044)'"
    )
    path: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Original scan path or file path"
    )
    image_base64: Optional[str] = Field(
        default=None,
        description="Optional base64-encoded CT scan image"
    )

    @model_validator(mode="after")
    def check_at_least_one_input(self):
        has_text = bool((self.image_id and self.image_id.strip()) or (self.path and self.path.strip()))
        has_image = bool(self.image_base64 and self.image_base64.strip())
        if not has_text and not has_image:
            raise ValueError("At least one input feature ('image_id', 'path', or 'image_base64') must be provided.")
        return self


class PredictionResponse(BaseModel):
    prediction: str = Field(..., description="Predicted diagnostic class: Cyst, Normal, Stone, or Tumor")
    confidence: float = Field(..., description="Prediction confidence score between 0.0 and 1.0")
    confidence_percentage: str = Field(..., description="Formatted confidence percentage string")
    class_probabilities: Dict[str, float] = Field(..., description="Probability distribution across all 4 classes")
    features_used: Dict[str, Any] = Field(..., description="Features utilized for inference")
    inference_mode: str = Field(..., description="Mode of inference executed")
    timestamp: str = Field(..., description="UTC timestamp of the prediction")


class HealthResponse(BaseModel):
    status: str = Field(..., description="Service status: healthy or degraded")
    model_loaded: bool = Field(..., description="Whether at least one model is loaded and ready")
    image_model_loaded: bool = Field(default=False, description="Whether the genuine visual feature image model is loaded")
    metadata_pipeline_loaded: bool = Field(default=False, description="Whether the metadata pipeline is loaded")
    model_type: str = Field(..., description="Type of machine learning pipeline loaded")
    supported_classes: List[str] = Field(..., description="Supported prediction classes")
    dataset_records: Optional[int] = Field(default=None, description="Total records in underlying dataset")
    evaluation_accuracy: Optional[float] = Field(default=None, description="Independent test accuracy of image classifier")
    evaluation_macro_f1: Optional[float] = Field(default=None, description="Independent test Macro-F1 of image classifier")
    test_samples: Optional[int] = Field(default=None, description="Number of independent held-out test samples evaluated")
    disclaimer: Optional[str] = Field(default=None, description="Safety and prototype medical disclaimer")
    version: str = Field(..., description="API version")


class ApiInfoResponse(BaseModel):
    title: str = Field(..., description="Application title")
    description: str = Field(..., description="Project description")
    version: str = Field(..., description="API version")
    supported_classes: List[str] = Field(..., description="Target diagnostic categories")
    endpoints: Dict[str, str] = Field(..., description="Primary API endpoints")


class SampleRecord(BaseModel):
    id: int
    image_id: str
    path: str
    diag: str
    target: int


class ErrorDetail(BaseModel):
    error: str
    detail: str
    code: int
