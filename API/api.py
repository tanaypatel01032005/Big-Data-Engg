from fastapi import FastAPI, HTTPException, Query
import sqlite3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cli_helper import setup_cli, check_help

# Check for --help early
check_help("FastAPI application for book library management.")

app = FastAPI()

DB_PATH = "D:\DAU\SEM 2\BDE\Assignment\Assignment 1\Assignment 1\Big-Data-Engg\Database\db.sqlite3"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

print(os.path.abspath("db.sqlite3"))

@app.get("/")
def root():
    return {"message": "Book Library API is working"}


@app.get("/books")
def get_books(
    limit: int = Query(1000, ge=1, le=5000, description="Number of books to fetch")
):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM books
        WHERE description IS NOT NULL
        ORDER BY Acc_Date DESC
        LIMIT ?
    """, (limit,))

    books = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return {
        "count": len(books),
        "data": books
    }


@app.get("/book")
def get_book_by_isbn(isbn: str):
    isbn = isbn.strip().replace("-", "")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM books
        WHERE REPLACE(ISBN, '-', '') = ?
    """, (isbn,))

    row = cursor.fetchone()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Book not found")

    return dict(row)


@app.get("/books/{isbn}")
def get_book_by_isbn_path(isbn: str):
    isbn = isbn.strip().replace("-", "")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM books
        WHERE REPLACE(ISBN, '-', '') = ?
    """, (isbn,))

    row = cursor.fetchone()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Book not found")

    return dict(row)


if __name__ == "__main__":
    args = setup_cli(
        "FastAPI application for book library management.",
        []
    )
    # Run the FastAPI app
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
