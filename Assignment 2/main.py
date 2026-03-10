from fastapi import FastAPI, Query, HTTPException, Path
from pydantic import BaseModel, Field
from typing import Optional, List

app = FastAPI()

# --- Mock Data (Base for the assignment) ---
products = [
    {"id": 1, "name": "Wireless Mouse", "price": 499, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Notebook", "price": 99, "category": "Stationery", "in_stock": True},
    {"id": 3, "name": "USB Hub", "price": 799, "category": "Electronics", "in_stock": False},
    {"id": 4, "name": "Pen Set", "price": 49, "category": "Stationery", "in_stock": True},
]

orders = []
feedback = []

# --- Base Endpoints (Fixes the 404 error) ---
@app.get("/")
def home():
    return {"message": "FastAPI Day 2 Assignment API is running!"}

@app.get("/products")
def get_all_products():
    """Returns the full list of products."""
    return products

# --- Q1: Filter Products with min_price ---
@app.get("/products/filter")
def filter_products(
    category: Optional[str] = Query(None),
    min_price: Optional[int] = Query(None, description="Minimum price"),
    max_price: Optional[int] = Query(None, description="Maximum price")
):
    """Filters products by category and price range."""
    result = products
    if category:
        result = [p for p in result if p["category"].lower() == category.lower()]
    if min_price is not None:
        result = [p for p in result if p["price"] >= min_price]
    if max_price is not None:
        result = [p for p in result if p["price"] <= max_price]
    return result

# --- Q2: Get Only Product Price ---
@app.get("/products/{product_id}/price")
def get_product_price(product_id: int = Path(..., gt=0)):
    """Returns only the name and price for a specific product ID."""
    for product in products:
        if product["id"] == product_id:
            return {"name": product["name"], "price": product["price"]}
    return {"error": "Product not found"}

# --- Q3: Customer Feedback (Pydantic + POST) ---
class CustomerFeedback(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=100)
    product_id: int = Field(..., gt=0)
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=300)

@app.post("/feedback")
def submit_feedback(data: CustomerFeedback):
    """Accepts and validates customer ratings (1-5) and comments."""
    feedback_entry = data.model_dump()
    feedback.append(feedback_entry)
    return {
        "message": "Feedback submitted successfully",
        "feedback": feedback_entry,
        "total_feedback": len(feedback)
    }

# --- Q4: Product Summary Dashboard ---
@app.get("/products/summary")
def get_product_summary():
    """Returns a dashboard of store statistics."""
    in_stock = [p for p in products if p["in_stock"]]
    out_stock = [p for p in products if not p["in_stock"]]
    expensive = max(products, key=lambda p: p["price"])
    cheapest = min(products, key=lambda p: p["price"])
    categories = list(set(p["category"] for p in products))
    
    return {
        "total_products": len(products),
        "in_stock_count": len(in_stock),
        "out_of_stock_count": len(out_stock),
        "most_expensive": {"name": expensive["name"], "price": expensive["price"]},
        "cheapest": {"name": cheapest["name"], "price": cheapest["price"]},
        "categories": categories
    }

# --- Q5: Bulk Orders (Pydantic + Business Logic) ---
class OrderItem(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, le=50)

class BulkOrder(BaseModel):
    company_name: str = Field(..., min_length=2)
    contact_email: str = Field(..., min_length=5)
    items: List[OrderItem] = Field(..., min_items=1)

@app.post("/orders/bulk")
def place_bulk_order(order: BulkOrder):
    """Processes multiple items, checking stock for each individually."""
    confirmed, failed = [], []
    grand_total = 0
    for item in order.items:
        product = next((p for p in products if p["id"] == item.product_id), None)
        if not product:
            failed.append({"product_id": item.product_id, "reason": "Product not found"})
        elif not product["in_stock"]:
            failed.append({"product_id": item.product_id, "reason": f"{product['name']} is out of stock"})
        else:
            subtotal = product["price"] * item.quantity
            grand_total += subtotal
            confirmed.append({"product": product["name"], "qty": item.quantity, "subtotal": subtotal})
            
    return {
        "company": order.company_name,
        "confirmed": confirmed,
        "failed": failed,
        "grand_total": grand_total
    }

# --- ⭐ BONUS: Order Status Tracker ---
class OrderRequest(BaseModel):
    product_id: int
    quantity: int

@app.post("/orders")
def place_order(request: OrderRequest):
    """Places a new order with an initial 'pending' status."""
    new_order = {
        "order_id": len(orders) + 1,
        "product_id": request.product_id,
        "quantity": request.quantity,
        "status": "pending"
    }
    orders.append(new_order)
    return new_order

@app.get("/orders/{order_id}")
def get_order(order_id: int):
    """Fetches a single order by its ID."""
    for order in orders:
        if order["order_id"] == order_id:
            return {"order": order}
    return {"error": "Order not found"}

@app.patch("/orders/{order_id}/confirm")
def confirm_order(order_id: int):
    """Updates an order status from 'pending' to 'confirmed'."""
    for order in orders:
        if order["order_id"] == order_id:
            order["status"] = "confirmed"
            return {"message": "Order confirmed", "order": order}
    raise HTTPException(status_code=404, detail="Order not found")