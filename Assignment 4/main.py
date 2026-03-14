from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Day 5 - Cart System Practice")

# --- In-Memory Database ---
products = [
    {"id": 1, "name": "Wireless Mouse", "price": 499, "in_stock": True},
    {"id": 2, "name": "Notebook", "price": 99, "in_stock": True},
    {"id": 3, "name": "USB Hub", "price": 299, "in_stock": False},
    {"id": 4, "name": "Pen Set", "price": 49, "in_stock": True}
]

cart = []
orders = []
order_counter = 1

# --- Pydantic Models ---
class CheckoutRequest(BaseModel):
    customer_name: str
    delivery_address: str


# --- Helper Function ---
def calculate_total(product: dict, quantity: int) -> int:
    return product["price"] * quantity


# --- Endpoints ---

@app.get("/")
def home():
    return {
        "message": "Welcome to the FastAPI Shopping Cart API",
    }

@app.post("/cart/add")
def add_to_cart(product_id: int, quantity: int):
    # Check if product exists
    product = next((p for p in products if p["id"] == product_id), None)
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    # Check if product is in stock (Q3 requirement)
    if not product["in_stock"]:
        raise HTTPException(
            status_code=400,
            detail=f"{product['name']} is out of stock"
        )

    # Check for duplicates to update quantity instead of appending (Q4 requirement)
    for item in cart:
        if item["product_id"] == product_id:
            item["quantity"] += quantity
            item["subtotal"] = calculate_total(product, item["quantity"])
            return {"message": "Cart updated", "cart_item": item}

    # Add new item to cart (Q1 requirement)
    new_item = {
        "product_id": product["id"],
        "product_name": product["name"],
        "quantity": quantity,
        "unit_price": product["price"],
        "subtotal": calculate_total(product, quantity)
    }
    cart.append(new_item)
    
    return {"message": "Added to cart", "cart_item": new_item}


@app.get("/cart")
def view_cart():
    # If cart is empty, return simple message (Q5 requirement)
    if not cart:
        return {"message": "Cart is empty"}
        
    # Calculate grand total (Q2 requirement)
    grand_total = sum(item["subtotal"] for item in cart)
    
    return {
        "items": cart,
        "item_count": len(cart), # Unique products, not total quantity
        "grand_total": grand_total
    }


@app.delete("/cart/{product_id}")
def remove_from_cart(product_id: int):
    global cart
    
    # Filter out the item with the given product_id (Q5 requirement)
    initial_length = len(cart)
    cart = [item for item in cart if item["product_id"] != product_id]
    
    if len(cart) == initial_length:
        raise HTTPException(status_code=404, detail="Item not found in cart")
        
    return {"message": "Item removed from cart"}


@app.post("/cart/checkout")
def checkout(request: CheckoutRequest):
    global order_counter
    
    # Bonus: Empty cart check
    if not cart:
        raise HTTPException(
            status_code=400,
            detail="Cart is empty — add items first"
        )
        
    grand_total = sum(item["subtotal"] for item in cart)
    new_orders = []
    
    # Create an order for each distinct item in the cart (Q5 & Q6 requirement)
    for item in cart:
        order = {
            "order_id": order_counter,
            "customer_name": request.customer_name,
            "delivery_address": request.delivery_address,
            "product": item["product_name"],
            "quantity": item["quantity"],
            "total_price": item["subtotal"]
        }
        orders.append(order)
        new_orders.append(order)
        order_counter += 1
        
    # Clear the cart after checkout
    cart.clear()
    
    return {
        "message": "Checkout successful",
        "orders_placed": new_orders,
        "grand_total": grand_total
    }


@app.get("/orders")
def get_orders():
    # Returns the comprehensive list of orders (Q6 requirement)
    return {
        "orders": orders,
        "total_orders": len(orders)
    }