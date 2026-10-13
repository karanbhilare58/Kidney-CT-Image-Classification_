# Chronic Kidney Disease Analysis - Backend

FastAPI backend service providing machine learning inference and diagnostic classification for Chronic Kidney Disease analysis.

## Features

- **Diagnostic Target**: Multi-class classification into `Cyst`, `Normal`, `Stone`, and `Tumor`.
- **Reproducible Pipeline**: Scikit-Learn TF-IDF and Logistic Regression pipeline saved as a Joblib artifact (`backend/models/kidney_pipeline.joblib`).
- **REST Endpoints**:
  - `GET /`: API metadata and available diagnostic classes.
  - `GET /health`: Model availability and health status.
  - `GET /features`: Input feature specifications, data types, and sample inputs.
  - `POST /predict`: Structured input inference with class probability distributions.
  - `POST /predict/image`: Multipart CT scan image upload inference.
  - `GET /samples`: Real dataset sample records for testing.
  - `GET /docs`: Automatic interactive Swagger documentation.

## Installation & Setup

1. Create and activate a Python virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. (Optional) Re-train the model pipeline:
   ```bash
   python3 train.py
   ```

4. Run the backend server:
   ```bash
   uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

5. Access interactive Swagger API documentation:
   - [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
