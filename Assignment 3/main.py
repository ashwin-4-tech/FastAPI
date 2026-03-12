from fastapi import FastAPI, status, Response, Query
from pydantic import BaseModel

app = FastAPI()

# Reconstructed base data to match the expected outputs from the assignment
products = [
    {"id": 1, "name": "Wireless Mouse", "price": 499, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Keyboard", "price": 99, "category": "Electronics", "in_stock": True},
    {"id": 3, "name": "USB Hub", "price": 799, "category": "Electronics", "in_stock": False},
    {"id": 4, "name": "Pen Set", "price": 49, "category": "Stationery", "in_stock": True}
]

class NewProduct(BaseModel):
    name: str
    price: int
    category: str
    in_stock: bool = True

def find_product(product_id: int):
    return next((p for p in products if p['id'] == product_id), None)

# -------------------------------------------------------------------
# NEW ENDPOINTS (Must be placed ABOVE the /{product_id} routes)
# -------------------------------------------------------------------
@app.get("/")
def home():
    return {"message": "Welcome to the Day 4 Assignment API! Go to /docs to begin."}

    
# Q5: GET /products/audit - Inventory Summary
@app.get('/products/audit')
def product_audit():
    in_stock_list  = [p for p in products if p['in_stock']]
    out_stock_list = [p for p in products if not p['in_stock']]
    stock_value    = sum(p['price'] * 10 for p in in_stock_list)
    priciest       = max(products, key=lambda p: p['price'])
    return {
        'total_products':    len(products),
        'in_stock_count':    len(in_stock_list),
        'out_of_stock_names': [p['name'] for p in out_stock_list],
        'total_stock_value':  stock_value,
        'most_expensive':    {'name': priciest['name'], 'price': priciest['price']},
    }

# BONUS: PUT /products/discount - Apply a Category-Wide Discount
@app.put('/products/discount')
def bulk_discount(
    category: str = Query(..., description='Category to discount'),
    discount_percent: int = Query(..., ge=1, le=99, description='% off'),
):
    updated = []
    for p in products:
        if p['category'] == category:
            p['price'] = int(p['price'] * (1 - discount_percent / 100))
            updated.append(p)
    if not updated:
        return {'message': f'No products found in category: {category}'}
    return {
        'message':          f'{discount_percent}% discount applied to {category}',
        'updated_count':    len(updated),
        'updated_products': updated,
    }

# -------------------------------------------------------------------
# EXISTING ENDPOINTS (For completing Q1 - Q4 via Swagger UI)
# -------------------------------------------------------------------

@app.get('/products')
def get_all_products():
    return {"products": products, "total": len(products)}

@app.post('/products', status_code=status.HTTP_201_CREATED)
def add_product(product: NewProduct, response: Response):
    # Check for duplicates to satisfy Q1 constraints
    if any(p['name'].lower() == product.name.lower() for p in products):
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": "Duplicate product name"}
        
    next_id = max(p['id'] for p in products) + 1 if products else 1
    new_prod_dict = {"id": next_id, **product.dict()}
    products.append(new_prod_dict)
    return {"message": "Product added", "product": new_prod_dict}

@app.get('/products/{product_id}')
def get_product(product_id: int, response: Response):
    product = find_product(product_id)
    if not product:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'error': 'Product not found'}
    return product

@app.put('/products/{product_id}')
def update_product(product_id: int, response: Response, price: int = None, in_stock: bool = None):
    product = find_product(product_id)
    if not product:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'error': 'Product not found'}
        
    if price is not None:
        product['price'] = price
    if in_stock is not None:
        product['in_stock'] = in_stock
        
    return {"message": "Product updated", "product": product}

@app.delete('/products/{product_id}')
def delete_product(product_id: int, response: Response):
    product = find_product(product_id)
    if not product:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'error': 'Product not found'}
    products.remove(product)
    return {'message': f"Product '{product['name']}' deleted"}