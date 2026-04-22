# Bristol Regional Food Network - API Documentation

## Authentication
All cart and order endpoints require authentication. Log in via:
- Django admin: http://localhost:8000/admin/
- Browsable API: http://localhost:8000/api/cart/ (click "Log in")

## Endpoints

### Products
- **GET /api/products/** - List all available products
  - Query params: `?category=vegetables`, `?search=tomato`, `?producer=username`
- **GET /api/products/{id}/** - Get single product details

### Categories
- **GET /api/categories/** - List all active categories
- **GET /api/categories/{id}/** - Get single category

### Shopping Cart
- **GET /api/cart/** - Get current user's cart
- **POST /api/cart/add_item/** - Add product to cart
  ```json
  {
    "product_id": 1,
    "quantity": 2
  }