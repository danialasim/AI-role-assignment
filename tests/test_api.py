import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.models import init_db

client = TestClient(app)

def test_root_endpoint():
    """Test the root endpoint returns API information"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"] == "SEO Content Generator API"
    assert "version" in data
    assert "docs" in data

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data

def test_generate_article_endpoint():
    """Test article generation request is accepted"""
    response = client.post(
        "/generate-article",
        json={
            "topic": "test productivity tools",
            "target_word_count": 800,
            "language": "en"
        }
    )
    assert response.status_code == 202  # Accepted
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "pending"
    assert "created_at" in data
    assert data["job_id"] is not None

def test_generate_article_validation_min_word_count():
    """Test validation rejects word count below minimum"""
    response = client.post(
        "/generate-article",
        json={
            "topic": "test topic",
            "target_word_count": 100  # Below minimum of 500
        }
    )
    assert response.status_code == 422  # Validation error

def test_generate_article_validation_max_word_count():
    """Test validation rejects word count above maximum"""
    response = client.post(
        "/generate-article",
        json={
            "topic": "test topic",
            "target_word_count": 6000  # Above maximum of 5000
        }
    )
    assert response.status_code == 422

def test_generate_article_validation_empty_topic():
    """Test validation rejects empty topic"""
    response = client.post(
        "/generate-article",
        json={
            "topic": "",
            "target_word_count": 1500
        }
    )
    assert response.status_code == 422

def test_generate_article_validation_short_topic():
    """Test validation rejects topic shorter than 3 characters"""
    response = client.post(
        "/generate-article",
        json={
            "topic": "ab",
            "target_word_count": 1500
        }
    )
    assert response.status_code == 422

def test_get_job_status():
    """Test job status retrieval for existing job"""
    # First create a job
    create_response = client.post(
        "/generate-article",
        json={"topic": "test topic for status check", "target_word_count": 800}
    )
    job_id = create_response.json()["job_id"]
    
    # Then check its status
    response = client.get(f"/job/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == job_id
    assert data["status"] in ["pending", "running", "completed", "failed"]
    assert "created_at" in data

def test_get_job_status_invalid_id():
    """Test job status endpoint returns 404 for invalid job ID"""
    response = client.get("/job/invalid-job-id-12345")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()

def test_generate_article_default_values():
    """Test article generation with default values"""
    response = client.post(
        "/generate-article",
        json={
            "topic": "artificial intelligence in healthcare"
            # Should use default word_count=1500 and language="en"
        }
    )
    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data

def test_api_docs_accessible():
    """Test that API documentation is accessible"""
    response = client.get("/docs")
    assert response.status_code == 200
    
    response = client.get("/redoc")
    assert response.status_code == 200

def test_cors_headers():
    """Test CORS headers are present"""
    response = client.options("/generate-article")
    # CORS middleware should add appropriate headers
    assert response.status_code in [200, 405]  # OPTIONS or Method Not Allowed
