import BookTile from "./BookTile";

export default function BookGrid({ title, books = [], onSelect }) {
  return (
    <section style={{ marginBottom: "36px" }}>
      {title && <h2>{title}</h2>}

      <div className="book-grid">
        {books.length === 0 && (
          <div className="empty-state">
            <div className="empty-icon">📭</div>
            <p>No books found. Try a different search term.</p>
          </div>
        )}

        {books.map((book, idx) => (
          <BookTile
            key={book.acc_no || book.Acc_No || idx}
            book={book}
            onSelect={onSelect}
          />
        ))}
      </div>
    </section>
  );
}
