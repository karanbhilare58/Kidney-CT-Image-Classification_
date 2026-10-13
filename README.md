# Kidney CT Image Condition Classification — PyTorch

An end-to-end deep learning application for classifying kidney CT images into four dataset categories: **Normal, Cyst, Stone, and Tumor** using **PyTorch**, **torchvision VGG16**, a **FastAPI** backend, and a **React + Vite** frontend.

---

## Overview

This project provides an automated pipeline for kidney CT image analysis:
- **PyTorch Transfer Learning Pipeline:** Loads images locally from folder-based directories, groups exact duplicate content hashes to prevent cross-split data leakage, applies inverse-frequency weighted cross-entropy loss, and trains a VGG16 model with frozen feature extractors.
- **FastAPI REST API:** Serves the PyTorch model checkpoint with strict validation, real-time image preprocessing, and graceful error handling.
- **React Frontend Dashboard:** Interactive medical dashboard allowing users to upload CT scans, view predicted categories, inspect confidence distributions across all four findings, and review image density metrics.


---

## Dataset Structure & Leakage Prevention

The model loads directly from the local directory:

```text
CT-KIDNEY-DATASET-Normal-Cyst-Tumor-Stone/
├── Cyst/     (3,709 images)
├── Normal/   (5,077 images)
├── Stone/    (1,377 images)
└── Tumor/    (2,283 images)
Total: 12,446 images (.jpg)
```

### Data Leakage Safeguards
- **Exact Binary Duplicates:** An audit identified 517 exact binary duplicate files (matching MD5 content hashes) within class folders. To eliminate direct train-to-test data leakage, files are grouped by exact MD5 hash before partitioning, ensuring no duplicate image appears across splits.
- **Deterministic 70 / 15 / 15 Partitioning:**
  - **Training Split (70%):** 8,350 unique images
  - **Validation Split (15%):** 1,789 unique images
  - **Held-Out Test Split (15%):** 1,790 unique images
  - Zero hash overlap between splits ($\text{Train} \cap \text{Val} = \emptyset, \text{Train} \cap \text{Test} = \emptyset, \text{Val} \cap \text{Test} = \emptyset$).
- **Patient-Level Generalization Limitation:** The public benchmark dataset flattened all images as `<Class>- (<Index>).jpg` without retaining DICOM headers, patient identifiers, or series numbers. Consequently, adjacent CT slices from the same patient scan may exist across samples.

---

## Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Deep Learning** | PyTorch 2.x, torchvision (VGG16), PIL, NumPy, Scikit-Learn |
| **Backend API** | FastAPI, Uvicorn, Pydantic, python-multipart |
| **Frontend UI** | React 18, Vite, Lucide React, Vanilla CSS |
| **Testing** | Pytest, FastAPI TestClient |
| **Environment** | Python 3.13 / Linux (Ubuntu) |

---

## Setup & Installation on Ubuntu / Linux

### 1. Prerequisites
Verify system installations:
```bash
python3 --version   # Python 3.10+
node -v             # Node.js 18+
npm -v              # npm 9+
```

### 2. Configure Virtual Environment & Dependencies
From the project root:
```bash
# Create local virtual environment
python3 -m venv .venv

# Activate environment
source .venv/bin/activate

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Register Jupyter Kernel
To run notebooks in Antigravity IDE or Jupyter:
```bash
python -m ipykernel install --user --name=kidney-ct-pytorch --display-name="Python (Kidney CT PyTorch .venv)"
```
In Antigravity IDE, select **`Python (Kidney CT PyTorch .venv)`** as the active notebook kernel.

---

## Model Training & Checkpoint Creation

The training workflow is implemented in [`Chronic_kidney_disease_PyTorch.ipynb`](Chronic_kidney_disease_PyTorch.ipynb):

1. Open `Chronic_kidney_disease_PyTorch.ipynb` and select kernel `Python (Kidney CT PyTorch .venv)`.
2. **Smoke Test vs. Full Training:**
   - In Cell 2:
     - `SMOKE_TEST = True`: Quick 2-epoch verification run over 32 samples per class (~128 total) to verify pipeline gradients, evaluation, and checkpoint saving.
     - `SMOKE_TEST = False`: Full training run across all 8,350 unique training images (takes ~53 minutes per epoch on CPU; recommended on GPU).
3. The notebook automatically saves:
   - `kidney_model.pth` — Includes model weights (`model_state_dict`), architecture (`vgg16`), class mapping, input size (224), normalization constants, and evaluation accuracy.
   - `best_kidney_model.pth` — State dictionary of the best validation loss checkpoint.

---

## Running the Application

### 1. Start the FastAPI Backend
In terminal 1:
```bash
cd ~/Desktop/Chronic-Kidney-Diease-Analysis-
source .venv/bin/activate
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
The backend initializes the PyTorch model checkpoint on startup and exposes:
- **API Base:** `http://127.0.0.1:8000`
- **Interactive Swagger Docs:** `http://127.0.0.1:8000/docs`
- **Health Check:** `http://127.0.0.1:8000/health`

### 2. Start the React Frontend
In terminal 2:
```bash
cd ~/Desktop/Chronic-Kidney-Diease-Analysis-/frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

### 3. Running Predictions
- Navigate to the **Primary CT Scan Analysis** tab.
- Drag and drop or upload any CT scan image (e.g., `CT-KIDNEY-DATASET-Normal-Cyst-Tumor-Stone/Cyst/Cyst- (590).jpg`).
- Click **Run Genuine CT Visual Inference** to view predicted class, confidence, and full probability distribution.
- Alternatively, select any of the **Demo CT Scan Fixtures** buttons to generate an in-memory synthetic test image and verify the model pipeline.

---

## Automated Backend Testing

Run the comprehensive Pytest suite:
```bash
source .venv/bin/activate
pytest backend/tests/test_api.py -v
```

The 18 automated tests verify:
- PyTorch model checkpoint loading and state configuration
- Image preprocessing and tensor normalization $(1, 3, 224, 224)$
- Prediction output shape $(1, 4)$ and probability distribution summing to $1.0$
- Valid inference on CT images (`Normal`, `Cyst`, `Stone`, `Tumor`) using programmatic synthetic test fixtures
- Base64 image payload handling via `POST /predict`
- Rejection of empty $0$-byte files (`HTTP 400`)
- Rejection of non-image MIME types (`HTTP 400`)
- Rejection of corrupted image bytes (`HTTP 400`)
- Graceful handling when model checkpoint is missing (`HTTP 503`)
- Dataset metadata explorer search (with programmatic fallbacks when index CSV is excluded)

---

## Frontend Build Verification

To verify frontend compilation for production:
```bash
cd frontend
npm run build
```
Builds static bundles to `frontend/dist/` with zero errors.

---

## Dataset Attribution & License

- **Benchmark Dataset:** [CT KIDNEY DATASET: Normal-Cyst-Tumor and Stone](https://www.kaggle.com/datasets/nazmulhasan1975/ct-kidney-dataset-normal-cyst-tumor-and-stone)
- **Dataset License:** [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)
- **Primary Citation:**  
  Islam, M. N., Hasan, M., Hossain, M. K., Alam, M. G. R., Uddin, M. Z., & Soylu, A. (2022). *Vision transformer and explainable transfer learning models for auto detection of kidney cyst, stone and tumor from CT-radiography*. **Scientific Reports**, 12(1), 1–14. [DOI: 10.1038/s41598-022-26177-3](https://doi.org/10.1038/s41598-022-26177-3)
- **Asset Exclusion & Licensing Compliance Notice:**  
  To strictly comply with data distribution standards and avoid redistributing third-party assets whose individual licensing or origin chain cannot be independently verified, the following items are excluded from Git via `.gitignore`:
  - **Sample CT Images & Crops (`backend/sample_images/`, `frontend/public/samples/`):** The six bundled sample images are cropped derivatives without verified individual redistribution licenses. They have been replaced in tests and demo buttons with programmatic synthetic fixtures and graceful fallbacks. The original local files remain preserved locally.
  - **Dataset Index CSV (`kidneyData.csv`):** This file is an extracted notebook index containing local Google Colab paths and is not part of the canonical upstream dataset distribution. It is excluded from the repository, while preserved locally on disk. The API `/samples` endpoint falls back to static verified sample schemas if the CSV is not present.
  - **Raw Benchmark Dataset (`CT-KIDNEY-DATASET-Normal-Cyst-Tumor-Stone/`):** All 12,446 raw CT slices (~1.2 GB) remain local and excluded. Users should obtain the dataset directly from the benchmark author on Kaggle under CC BY 4.0.
  - **Trained Model Checkpoints (`*.pth`, `*.pt`):** Large binary PyTorch model weights (~512 MB each) are excluded from Git tracking.
- **Scope & Clinical Disclaimer:**  
  This repository is developed strictly for educational and academic research purposes. It provides a computer vision image-finding classifier and is **not** a clinically validated diagnostic system. It does not stage or clinically diagnose Chronic Kidney Disease (CKD).

---

## Author & Project Information

- **Project:** Kidney CT Image Condition Classification
- **Repository:** [Kidney-CT-Image-Classification](https://github.com/karanbhilare58/Kidney-CT-Image-Classification)

