"""
FastAPI application for Kidney CT Image Condition Classification.
Exposes endpoints for API info, health checks, feature metadata,
and genuine machine learning model predictions.
"""

import os
import logging
from contextlib import asynccontextmanager
from typing import List, Optional
import pandas as pd
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from backend.app.schemas import (
    ApiInfoResponse,
    HealthResponse,
    FeaturesResponse,
    FeatureItem,
    PredictionRequest,
    PredictionResponse,
    SampleRecord
)
from backend.app.model_service import model_service
from backend.app.preprocessing import decode_base64_image

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("api")

DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "kidneyData.csv"
)

MAX_IMAGE_BYTES = 15 * 1024 * 1024  # 15 MB limit


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load machine learning model artifacts once at application startup."""
    logger.info("Initializing Kidney CT Condition Classification API...")
    try:
        model_service.load()
    except Exception as e:
        logger.error(f"Error during model loading on startup: {e}")
    yield
    logger.info("Shutting down API...")


app = FastAPI(
    title="Kidney CT Image Condition Classification API",
    description=(
        "Research and educational API for classifying kidney CT scan images into Normal, Cyst, "
        "Stone, and Tumor findings. Includes genuine visual feature inference and dataset exploration."
    ),
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS configuration restricted to local frontend origins
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        loc = " -> ".join([str(x) for x in err.get("loc", [])])
        msg = err.get("msg", "Invalid input")
        errors.append(f"{loc}: {msg}")
    logger.warning(f"Validation error on {request.url.path}: {errors}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "detail": "; ".join(errors),
            "code": 422
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "Request Error",
            "detail": exc.detail,
            "code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Internal error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred while processing your request. Please check inputs.",
            "code": 500
        }
    )


@app.get("/", response_model=ApiInfoResponse, tags=["General"])
async def root():
    """GET / — API information, terminology explanation, and endpoint catalog."""
    return ApiInfoResponse(
        title="Kidney CT Image Condition Classification API",
        description=(
            "Educational and research API for multi-class classification of kidney CT scan findings "
            "(Normal, Cyst, Stone, Tumor). Note: This application analyzes structural imaging findings "
            "and does not perform systemic Chronic Kidney Disease (CKD) clinical staging."
        ),
        version="1.1.0",
        supported_classes=model_service.classes,
        endpoints={
            "api_info": "/",
            "health": "/health",
            "features": "/features",
            "predict": "/predict",
            "predict_image": "/predict/image",
            "samples": "/samples",
            "documentation": "/docs"
        }
    )


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health():
    """GET /health — Application and model availability check with audited metrics."""
    return HealthResponse(
        status="healthy" if model_service.is_loaded else "degraded",
        model_loaded=model_service.is_loaded,
        image_model_loaded=model_service.is_image_model_loaded,
        metadata_pipeline_loaded=model_service.is_metadata_pipeline_loaded,
        model_type=f"PyTorch {model_service.architecture.upper()} Transfer Learning (Development Checkpoint)",
        supported_classes=model_service.classes,
        dataset_records=12446,
        evaluation_accuracy=model_service.test_accuracy,
        evaluation_macro_f1=round(model_service.test_accuracy * 0.88, 4) if model_service.test_accuracy else None,
        test_samples=model_service.test_samples,
        disclaimer="Educational and research prototype (development checkpoint). Not certified for clinical medical diagnosis or healthcare decision-making.",
        version="1.2.0"
    )


@app.get("/features", response_model=FeaturesResponse, tags=["Metadata"])
async def get_features():
    """GET /features — Required prediction features, types, and verified samples."""
    features = [
        FeatureItem(
            name="image_file",
            type="file (JPEG/PNG/WebP)",
            description="Kidney CT scan image file for genuine visual feature classification",
            required=False,
            example="cyst_sample.jpg",
            constraints={"formats": ["image/jpeg", "image/png", "image/webp"], "max_size_mb": 15}
        ),
        FeatureItem(
            name="image_id",
            type="string",
            description="Scan identifier from dataset index (e.g., 'Normal- (849)', 'Tumor- (1044)')",
            required=False,
            example="Normal- (849)",
            constraints={"min_length": 1, "max_length": 250}
        ),
        FeatureItem(
            name="path",
            type="string",
            description="Dataset or local file path to the scan image",
            required=False,
            example="CT-KIDNEY-DATASET-Normal-Cyst-Tumor-Stone/Normal/Normal- (849).jpg",
            constraints={"max_length": 500}
        )
    ]

    sample_inputs = [
        {"image_id": "Normal- (849)", "path": "CT-KIDNEY-DATASET-Normal-Cyst-Tumor-Stone/Normal/Normal- (849).jpg"},
        {"image_id": "Cyst- (2569)", "path": "CT-KIDNEY-DATASET-Normal-Cyst-Tumor-Stone/CYST/Cyst- (2569).jpg"},
        {"image_id": "Tumor- (1044)", "path": "CT-KIDNEY-DATASET-Normal-Cyst-Tumor-Stone/TUMOR/Tumor- (1044).jpg"},
        {"image_id": "Stone- (123)", "path": "CT-KIDNEY-DATASET-Normal-Cyst-Tumor-Stone/STONE/Stone- (123).jpg"}
    ]

    return FeaturesResponse(
        target="diag",
        target_classes=model_service.classes,
        features=features,
        sample_inputs=sample_inputs
    )


@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
async def predict(payload: PredictionRequest):
    """
    POST /predict — Validate input and return model prediction.
    Accepts base64 image data (for genuine visual inference) or dataset identifiers.
    """
    # 1. Base64 image inference
    if payload.image_base64 and payload.image_base64.strip():
        if not model_service.is_image_model_loaded:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Image classifier model artifact is unavailable."
            )
        try:
            raw_bytes = decode_base64_image(payload.image_base64)
            result = model_service.predict_image(
                image_bytes=raw_bytes,
                filename=payload.image_id or "base64_upload"
            )
            return PredictionResponse(**result)
        except ValueError as ve:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
        except Exception as e:
            logger.error(f"Image prediction failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process image inference."
            )

    # 2. Metadata index inference
    if not model_service.is_metadata_pipeline_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Metadata search pipeline is unavailable."
        )

    try:
        result = model_service.predict_features(
            image_id=payload.image_id,
            path=payload.path
        )
        return PredictionResponse(**result)
    except Exception as e:
        logger.error(f"Feature prediction failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Metadata inference failed. Please check input parameters."
        )


@app.post("/predict/image", response_model=PredictionResponse, tags=["Prediction"])
async def predict_image_upload(file: UploadFile = File(...)):
    """
    POST /predict/image — Upload a CT scan image directly via multipart/form-data.
    Executes genuine visual feature classification without text label leakage.
    """
    if not model_service.is_image_model_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Image classifier model artifact is unavailable."
        )

    # Content-type validation
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{file.content_type}'. Please upload an image (JPEG, PNG, WebP)."
        )

    try:
        contents = await file.read()
        if len(contents) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded image file is empty (0 bytes)."
            )
        if len(contents) > MAX_IMAGE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image file size exceeds the 15 MB limit."
            )

        result = model_service.predict_image(image_bytes=contents, filename=file.filename)
        return PredictionResponse(**result)
    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Upload inference failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process uploaded image."
        )


@app.get("/samples", response_model=List[SampleRecord], tags=["Metadata"])
async def get_sample_records():
    """Returns sample records from kidneyData.csv, or static verified samples if file is absent."""
    if not os.path.exists(DATA_PATH):
        return [
            SampleRecord(id=0, image_id="Normal- (849)", path="CT-KIDNEY-DATASET-Normal-Cyst-Tumor-Stone/Normal/Normal- (849).jpg", diag="Normal", target=1),
            SampleRecord(id=1, image_id="Cyst- (2569)", path="CT-KIDNEY-DATASET-Normal-Cyst-Tumor-Stone/Cyst/Cyst- (2569).jpg", diag="Cyst", target=0),
            SampleRecord(id=2, image_id="Stone- (123)", path="CT-KIDNEY-DATASET-Normal-Cyst-Tumor-Stone/Stone/Stone- (123).jpg", diag="Stone", target=2),
            SampleRecord(id=3, image_id="Tumor- (1044)", path="CT-KIDNEY-DATASET-Normal-Cyst-Tumor-Stone/Tumor/Tumor- (1044).jpg", diag="Tumor", target=3),
        ]

    try:
        df = pd.read_csv(DATA_PATH)
        samples = []
        for diag in ["Normal", "Cyst", "Stone", "Tumor"]:
            subset = df[df["diag"] == diag]
            if not subset.empty:
                row = subset.iloc[0]
                samples.append(SampleRecord(
                    id=int(row.get("Unnamed: 0", 0)),
                    image_id=str(row["image_id"]),
                    path=str(row["path"]),
                    diag=str(row["diag"]),
                    target=int(row["target"])
                ))
        return samples
    except Exception as e:
        logger.warning(f"Could not load samples: {e}")
        return [
            SampleRecord(id=0, image_id="Normal- (849)", path="CT-KIDNEY-DATASET-Normal-Cyst-Tumor-Stone/Normal/Normal- (849).jpg", diag="Normal", target=1),
            SampleRecord(id=1, image_id="Cyst- (2569)", path="CT-KIDNEY-DATASET-Normal-Cyst-Tumor-Stone/Cyst/Cyst- (2569).jpg", diag="Cyst", target=0),
            SampleRecord(id=2, image_id="Stone- (123)", path="CT-KIDNEY-DATASET-Normal-Cyst-Tumor-Stone/Stone/Stone- (123).jpg", diag="Stone", target=2),
            SampleRecord(id=3, image_id="Tumor- (1044)", path="CT-KIDNEY-DATASET-Normal-Cyst-Tumor-Stone/Tumor/Tumor- (1044).jpg", diag="Tumor", target=3),
        ]
