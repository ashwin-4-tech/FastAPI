from fastapi import FastAPI, Response, Query, status
from pydantic import BaseModel, Field
from typing import Optional, List
import math

app = FastAPI(title="Library Book Management System")

# --- DATA MODELS (Task 2 & 4) ---
# In-memory storage for Books and Members
books = [
    {"id": 1, "title": "The Great Gatsby", "author": "F. Scott Fitzgerald", "category": "Fiction", "is_available": True},
    {"id": 2, "title": "1984", "author": "George Orwell", "category": "Dystopian", "is_available": True},
    {"id": 3, "title": "The Hobbit", "author": "J.R.R. Tolkien", "category": "Fantasy", "is_available": False},
    {"id": 4, "title": "Sapiens", "author": "Yuval Noah Harari", "category": "History", "is_available": True},
    {"id": 5, "title": "Educated", "author": "Tara Westover", "category": "Memoir", "is_available": True},
    {"id": 6, "title": "Dune", "author": "Frank Herbert", "category": "Sci-Fi", "is_available": True},
]

members = []
member_counter = 1
borrow_records = []  # Day 5: Multi-step workflow storage

# --- PYDANTIC MODELS (Day 2 & 4 Concepts) ---
class MemberRequest(BaseModel):
    # Task 6: Request validation with Field constraints
    name: str = Field(..., min_length=2)
    email: str
    membership_type: str = "Standard"  # Task 9: Default value

class NewBook(BaseModel):
    # Task 11: Create new records
    title: str = Field(..., min_length=2)
    author: str = Field(..., min_length=2)
    category: str = Field(..., min_length=2)
    is_available: bool = True

class BorrowRequest(BaseModel):
    # Task 15: Checkout/Workflow model
    member_id: int
    book_id: int

# --- HELPER FUNCTIONS (Day 3 Concepts) ---
def find_book(book_id: int):
    """Helper to find a book by ID (Task 7)."""
    for book in books:
        if book["id"] == book_id:
            return book
    return None

def filter_books_logic(category: str = None, is_available: bool = None):
    """Helper for complex filtering (Task 10)."""
    filtered = books
    if category:
        filtered = [b for b in filtered if b["category"].lower() == category.lower()]
    if is_available is not None:
        filtered = [b for b in filtered if b["is_available"] == is_available]
    return filtered

# --- 1. BEGINNER: GET APIs (Task 1-5) ---

@app.get("/")
def home():
    # Task 1: Basic Home Route
    return {"message": "Welcome to City Public Library"}

@app.get("/books/summary")
def get_book_summary():
    # Task 5: Summary endpoint (Placed above /{id} to avoid conflicts)
    categories = list(set([b["category"] for b in books]))
    return {
        "total_books": len(books),
        "available": len([b for b in books if b["is_available"]]),
        "categories": categories
    }

@app.get("/books")
def list_books():
    # Task 2: List all records
    return {"total": len(books), "books": books}

@app.get("/books/{book_id}")
def get_book_by_id(book_id: int):
    # Task 3: Get record by ID
    book = find_book(book_id)
    if book:
        return book
    return {"error": "Book not found"}

@app.get("/members")
def list_members():
    # Task 4: List members
    return {"total_members": len(members), "members": members}

# --- 2. EASY: POST & HELPERS (Task 6-10) ---

@app.post("/members")
def add_member(member: MemberRequest):
    # Task 8: Create member using helper logic and Pydantic validation
    global member_counter
    new_member = member.dict()
    new_member["id"] = member_counter
    members.append(new_member)
    member_counter += 1
    return new_member

@app.get("/books/filter")
def filter_books(category: Optional[str] = None, available: Optional[bool] = None):
    # Task 10: Filtering with Query params
    results = filter_books_logic(category, available)
    return {"count": len(results), "books": results}

# --- 3. MEDIUM: CRUD & WORKFLOW (Task 11-15) ---

@app.post("/books", status_code=201)
def create_book(book: NewBook, response: Response):
    # Task 11: Add item with duplicate check and 201 status
    if any(b["title"].lower() == book.title.lower() for b in books):
        response.status_code = 400
        return {"error": "Book title already exists"}
    
    new_id = max([b["id"] for b in books]) + 1
    book_data = book.dict()
    book_data["id"] = new_id
    books.append(book_data)
    return book_data

@app.put("/books/{book_id}")
def update_book(book_id: int, price: Optional[int] = None, is_available: Optional[bool] = None):
    # Task 12: Partial Update (PUT)
    book = find_book(book_id)
    if not book:
        return {"error": "Not Found", "status": 404}
    if is_available is not None:
        book["is_available"] = is_available
    return book

@app.delete("/books/{book_id}")
def delete_book(book_id: int):
    # Task 13: Delete record
    book = find_book(book_id)
    if not book:
        return {"error": "Book not found"}
    books.remove(book)
    return {"message": f"Deleted book: {book['title']}"}

@app.post("/borrow")
def borrow_book(request: BorrowRequest):
    # Task 14 & 15: Multi-step workflow (Borrowing process)
    book = find_book(request.book_id)
    if not book or not book["is_available"]:
        return {"error": "Book is unavailable or does not exist"}
    
    # Mark as borrowed and record transaction
    book["is_available"] = False
    record = {"member_id": request.member_id, "book_id": request.book_id, "status": "borrowed"}
    borrow_records.append(record)
    return {"message": "Book borrowed successfully", "record": record}

# --- 4. HARD: SEARCH, SORT, PAGINATION (Task 16-20) ---

@app.get("/books/search")
def search_books(keyword: str):
    # Task 16: Keyword search across multiple fields
    results = [b for b in books if keyword.lower() in b["title"].lower() or keyword.lower() in b["author"].lower()]
    return {"total_found": len(results), "results": results if results else "No matches found"}

@app.get("/books/sort")
def sort_books(sort_by: str = "title", order: str = "asc"):
    # Task 17: Sorting logic
    valid_fields = ["title", "author", "category"]
    if sort_by not in valid_fields:
        return {"error": f"Invalid sort field. Choose from {valid_fields}"}
    
    reverse = True if order == "desc" else False
    sorted_books = sorted(books, key=lambda x: x[sort_by], reverse=reverse)
    return sorted_books

@app.get("/books/page")
def paginate_books(page: int = Query(1, ge=1), limit: int = Query(3, ge=1, le=10)):
    # Task 18: Pagination logic
    start = (page - 1) * limit
    end = start + limit
    total_pages = math.ceil(len(books) / limit)
    return {
        "page": page,
        "total_pages": total_pages,
        "items": books[start:end]
    }

# Task 19 & 20: Combined logic (Search + Sort for members)
@app.get("/members/search")
def search_members(name: str):
    results = [m for m in members if name.lower() in m["name"].lower()]
    return results