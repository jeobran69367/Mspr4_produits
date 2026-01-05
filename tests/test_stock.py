import pytest


def test_get_stock_by_product(client, sample_category):
    """Test getting stock for a product"""
    # Create a category and product
    cat_response = client.post("/api/v1/categories/", json=sample_category)
    category_id = cat_response.json()["id"]

    product_data = {"sku": "CAFE-001", "nom": "Café Arabica Premium", "categorie_id": category_id, "prix_ht": "15.99"}
    prod_response = client.post("/api/v1/products/", json=product_data)
    product_id = prod_response.json()["id"]

    # Get stock for product (should be auto-created)
    response = client.get(f"/api/v1/stock/product/{product_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["produit_id"] == product_id
    assert data["quantite_disponible"] == 0


def test_adjust_stock(client, sample_category):
    """Test adjusting stock quantity"""
    # Create a category and product
    cat_response = client.post("/api/v1/categories/", json=sample_category)
    category_id = cat_response.json()["id"]

    product_data = {"sku": "CAFE-001", "nom": "Café Arabica Premium", "categorie_id": category_id, "prix_ht": "15.99"}
    prod_response = client.post("/api/v1/products/", json=product_data)
    product_id = prod_response.json()["id"]

    # Adjust stock (add 100 units)
    adjustment = {"quantite": 100}
    response = client.post(f"/api/v1/stock/product/{product_id}/adjust", json=adjustment)
    assert response.status_code == 200
    data = response.json()
    assert data["quantite_disponible"] == 100


def test_low_stock_alert(client, sample_category):
    """Test low stock alert functionality"""
    # Create a category and product
    cat_response = client.post("/api/v1/categories/", json=sample_category)
    category_id = cat_response.json()["id"]

    product_data = {"sku": "CAFE-001", "nom": "Café Arabica Premium", "categorie_id": category_id, "prix_ht": "15.99"}
    prod_response = client.post("/api/v1/products/", json=product_data)
    product_id = prod_response.json()["id"]

    # Get stock
    stock_response = client.get(f"/api/v1/stock/product/{product_id}")
    stock = stock_response.json()

    # Stock should have alert (0 < 10 default minimum)
    assert stock["alerte_stock_bas"] is True

    # Add enough stock to clear alert
    adjustment = {"quantite": 50}
    client.post(f"/api/v1/stock/product/{product_id}/adjust", json=adjustment)

    # Check alert is cleared
    stock_response = client.get(f"/api/v1/stock/product/{product_id}")
    stock = stock_response.json()
    assert stock["alerte_stock_bas"] is False


def test_get_low_stock_alerts(client, sample_category):
    """Test getting all products with low stock"""
    # Create a category and product with low stock
    cat_response = client.post("/api/v1/categories/", json=sample_category)
    category_id = cat_response.json()["id"]

    product_data = {"sku": "CAFE-001", "nom": "Café Arabica Premium", "categorie_id": category_id, "prix_ht": "15.99"}
    client.post("/api/v1/products/", json=product_data)

    # Get low stock alerts
    response = client.get("/api/v1/stock/alerts")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["alerte_stock_bas"] is True


def test_negative_stock_prevention(client, sample_category):
    """Test that stock cannot go negative"""
    # Create a category and product
    cat_response = client.post("/api/v1/categories/", json=sample_category)
    category_id = cat_response.json()["id"]

    product_data = {"sku": "CAFE-001", "nom": "Café Arabica Premium", "categorie_id": category_id, "prix_ht": "15.99"}
    prod_response = client.post("/api/v1/products/", json=product_data)
    product_id = prod_response.json()["id"]

    # Try to remove more stock than available
    adjustment = {"quantite": -100}
    response = client.post(f"/api/v1/stock/product/{product_id}/adjust", json=adjustment)
    assert response.status_code == 400
