export default function BookModal({ book, onClose }) {
  if (!book) return null;

  const title = book.Title || "Untitled";
  const author = book.Author_Editor || "Unknown";
  const year = book.Year || "N/A";
  const isbn = book.ISBN || "N/A";
  const description = book.description || "No description available.";
  const pages = book.Pages || "N/A";
  const classNo = book.Class_No || "N/A";
  const accNo = book.Acc_No || "N/A";
  const imageUrl = book.image_url;
  const bookUrl = book.book_url;
  const similarity = book.similarity;
  const matches = book.matches || [];

  return (
    <div className="modal-overlay fade-in" onClick={onClose}>
      <div
        className="modal-content slide-down"
        onClick={(e) => e.stopPropagation()}
      >
        <button className="modal-close" onClick={onClose}>×</button>

        <div className="modal-header">
          {imageUrl ? (
            <img
              className="modal-cover"
              src={imageUrl}
              alt={`Cover of ${title}`}
              onError={(e) => {
                e.target.style.display = "none";
                e.target.nextElementSibling.style.display = "flex";
              }}
            />
          ) : null}
          <div
            className="tile-initial large"
            style={imageUrl ? { display: "none" } : {}}
          >
            {title.charAt(0).toUpperCase()}
          </div>

          <div className="modal-title-area">
            <h2>{title}</h2>
            <div className="modal-meta">{author} • {year}</div>
            {similarity != null && (
              <span className="score-pill" style={{ marginTop: "8px" }}>
                {(similarity * 100).toFixed(1)}% match
              </span>
            )}
          </div>
        </div>

        <div className="modal-body">
          <div className="modal-section">
            <label>Description</label>
            <p>{description}</p>
          </div>

          {matches.length > 0 && (
            <div className="modal-section">
              <label>Match Evidence</label>
              {matches.map((m, i) => (
                <div className="evidence-item" key={i}>
                  <span>{m.field}</span>
                  <p>{m.text?.substring(0, 200)}{m.text?.length > 200 ? "..." : ""}</p>
                  <small>Score: {(m.score * 100).toFixed(1)}%</small>
                </div>
              ))}
            </div>
          )}

          <div className="modal-details-grid">
            <div className="detail-item">
              <label>ISBN</label>
              <span>{isbn}</span>
            </div>
            <div className="detail-item">
              <label>Pages</label>
              <span>{pages}</span>
            </div>
            <div className="detail-item">
              <label>Class No.</label>
              <span>{classNo}</span>
            </div>
            <div className="detail-item">
              <label>Acc. No.</label>
              <span>{accNo}</span>
            </div>
          </div>

          {bookUrl && (
            <div className="modal-section" style={{ marginTop: "8px" }}>
              <a
                href={bookUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="book-link"
              >
                📖 View on Google Books →
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
