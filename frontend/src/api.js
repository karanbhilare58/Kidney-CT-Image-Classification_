/**
 * API client service for Chronic Kidney Disease Analysis backend.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

/**
 * Fetch general API info.
 */
export async function fetchApiInfo() {
  const response = await fetch(`${API_BASE_URL}/`);
  if (!response.ok) {
    throw new Error(`Failed to fetch API info (${response.status})`);
  }
  return response.json();
}

/**
 * Fetch backend health status.
 */
export async function fetchHealth() {
  const response = await fetch(`${API_BASE_URL}/health`);
  if (!response.ok) {
    throw new Error(`Backend unavailable (${response.status})`);
  }
  return response.json();
}

/**
 * Fetch feature metadata and constraints.
 */
export async function fetchFeatures() {
  const response = await fetch(`${API_BASE_URL}/features`);
  if (!response.ok) {
    throw new Error(`Failed to load features metadata (${response.status})`);
  }
  return response.json();
}

/**
 * Fetch genuine samples from kidneyData.csv.
 */
export async function fetchSamples() {
  const response = await fetch(`${API_BASE_URL}/samples`);
  if (!response.ok) {
    return [];
  }
  return response.json();
}

/**
 * Run prediction using structured features.
 */
export async function predictFeatures(payload) {
  const response = await fetch(`${API_BASE_URL}/predict`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  const data = await response.json();
  if (!response.ok) {
    const errorMsg = data.detail || data.error || `Prediction failed (${response.status})`;
    throw new Error(errorMsg);
  }
  return data;
}

/**
 * Run prediction using direct image file upload.
 */
export async function predictImageFile(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/predict/image`, {
    method: 'POST',
    body: formData,
  });

  const data = await response.json();
  if (!response.ok) {
    const errorMsg = data.detail || data.error || `Image prediction failed (${response.status})`;
    throw new Error(errorMsg);
  }
  return data;
}
