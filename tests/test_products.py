from decimal import Decimal

import pytest


def test_create_product(client, sample_category):
    """Test creating a new product"""
    # First create a category
    cat_response = client.post("/api/v1/categories/", json=sample_category)
    category_id = cat_response.json()["id"]

    product_data = {
        "sku": "CAFE-001",
        "nom": "Café Arabica Premium",
        "description": "Café Arabica d'exception",
        "categorie_id": category_id,
        "prix_ht": "15.99",
        "taux_tva": "20.0",
        "unite_mesure": "g",
        "poids_unitaire": "250",
        "fournisseur": "Fournisseur Test",
        "origine": "Colombie",
    }

    response = client.post("/api/v1/products/", json=product_data)
    assert response.status_code == 201
    data = response.json()
    assert data["sku"] == product_data["sku"]
    assert data["nom"] == product_data["nom"]
    assert "id" in data
    assert "prix_ttc" in data


def test_get_products(client, sample_category):
    """Test getting all products"""
    # Create a category and product
    cat_response = client.post("/api/v1/categories/", json=sample_category)
    category_id = cat_response.json()["id"]

    product_data = {"sku": "CAFE-001", "nom": "Café Arabica Premium", "categorie_id": category_id, "prix_ht": "15.99"}
    client.post("/api/v1/products/", json=product_data)

    # Get all products
    response = client.get("/api/v1/products/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


def test_get_product_by_id(client, sample_category):
    """Test getting a specific product"""
    # Create a category and product
    cat_response = client.post("/api/v1/categories/", json=sample_category)
    category_id = cat_response.json()["id"]

    product_data = {"sku": "CAFE-001", "nom": "Café Arabica Premium", "categorie_id": category_id, "prix_ht": "15.99"}
    create_response = client.post("/api/v1/products/", json=product_data)
    product_id = create_response.json()["id"]

    # Get the product
    response = client.get(f"/api/v1/products/{product_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == product_id


def test_update_product(client, sample_category):
    """Test updating a product"""
    # Create a category and product
    cat_response = client.post("/api/v1/categories/", json=sample_category)
    category_id = cat_response.json()["id"]

    product_data = {"sku": "CAFE-001", "nom": "Café Arabica Premium", "categorie_id": category_id, "prix_ht": "15.99"}
    create_response = client.post("/api/v1/products/", json=product_data)
    product_id = create_response.json()["id"]

    # Update the product
    update_data = {"nom": "Café Arabica Ultra Premium"}
    response = client.put(f"/api/v1/products/{product_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["nom"] == "Café Arabica Ultra Premium"


def test_delete_product(client, sample_category):
    """Test deleting a product"""
    # Create a category and product
    cat_response = client.post("/api/v1/categories/", json=sample_category)
    category_id = cat_response.json()["id"]

    product_data = {"sku": "CAFE-001", "nom": "Café Arabica Premium", "categorie_id": category_id, "prix_ht": "15.99"}
    create_response = client.post("/api/v1/products/", json=product_data)
    product_id = create_response.json()["id"]

    # Delete the product
    response = client.delete(f"/api/v1/products/{product_id}")
    assert response.status_code == 204

    # Verify deletion
    get_response = client.get(f"/api/v1/products/{product_id}")
    assert get_response.status_code == 404


def test_search_products(client, sample_category):
    """Test searching for products"""
    # Create a category and products
    cat_response = client.post("/api/v1/categories/", json=sample_category)
    category_id = cat_response.json()["id"]

    product1 = {"sku": "CAFE-001", "nom": "Café Arabica Premium", "categorie_id": category_id, "prix_ht": "15.99"}
    product2 = {"sku": "CAFE-002", "nom": "Café Robusta Standard", "categorie_id": category_id, "prix_ht": "12.99"}
    client.post("/api/v1/products/", json=product1)
    client.post("/api/v1/products/", json=product2)

    # Search for "Arabica"
    response = client.get("/api/v1/products/?search=Arabica")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert "Arabica" in data[0]["nom"]


def test_prix_ttc_calculation(client, sample_category):
    """Test that prix_ttc is correctly calculated"""
    # Create a category and product
    cat_response = client.post("/api/v1/categories/", json=sample_category)
    category_id = cat_response.json()["id"]

    product_data = {
        "sku": "CAFE-001",
        "nom": "Café Test",
        "categorie_id": category_id,
        "prix_ht": "10.00",
        "taux_tva": "20.0",
    }
    response = client.post("/api/v1/products/", json=product_data)
    data = response.json()

    # prix_ttc should be 12.00 (10.00 * 1.20)
    assert float(data["prix_ttc"]) == 12.00
