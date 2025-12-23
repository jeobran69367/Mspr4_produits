import pytest
from uuid import uuid4


def test_create_category(client, sample_category):
    """Test creating a new category"""
    response = client.post("/api/v1/categories/", json=sample_category)
    assert response.status_code == 201
    data = response.json()
    assert data["nom"] == sample_category["nom"]
    assert data["code"] == sample_category["code"]
    assert "id" in data


def test_get_categories(client, sample_category):
    """Test getting all categories"""
    # Create a category first
    client.post("/api/v1/categories/", json=sample_category)
    
    # Get all categories
    response = client.get("/api/v1/categories/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["nom"] == sample_category["nom"]


def test_get_category_by_id(client, sample_category):
    """Test getting a specific category"""
    # Create a category
    create_response = client.post("/api/v1/categories/", json=sample_category)
    category_id = create_response.json()["id"]
    
    # Get the category
    response = client.get(f"/api/v1/categories/{category_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == category_id
    assert data["nom"] == sample_category["nom"]


def test_update_category(client, sample_category):
    """Test updating a category"""
    # Create a category
    create_response = client.post("/api/v1/categories/", json=sample_category)
    category_id = create_response.json()["id"]
    
    # Update the category
    update_data = {"nom": "Arabica Premium"}
    response = client.put(f"/api/v1/categories/{category_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["nom"] == "Arabica Premium"


def test_delete_category(client, sample_category):
    """Test deleting a category"""
    # Create a category
    create_response = client.post("/api/v1/categories/", json=sample_category)
    category_id = create_response.json()["id"]
    
    # Delete the category
    response = client.delete(f"/api/v1/categories/{category_id}")
    assert response.status_code == 204
    
    # Verify deletion
    get_response = client.get(f"/api/v1/categories/{category_id}")
    assert get_response.status_code == 404


def test_create_duplicate_category_code(client, sample_category):
    """Test that duplicate category codes are not allowed"""
    client.post("/api/v1/categories/", json=sample_category)
    response = client.post("/api/v1/categories/", json=sample_category)
    assert response.status_code == 400
