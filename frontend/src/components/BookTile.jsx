export default function BookTile({ book, onSelect }) {
  const title = book.Title || "Untitled";
  const isbn = book.ISBN || "N/A";
  const description = book.description || "";
  const similarity = book.similarity;
  const imageUrl = book.image_url;

  return (
    <div
      className="book-tile stagger-in"
      tabIndex={0}
      onClick={() => onSelect?.(book)}
      onKeyDown={(e) => {
        if (e.key === "Enter") onSelect?.(book);
      }}
    >
      {similarity != null && (
        <div className="tile-score">{(similarity * 100).toFixed(0)}%</div>
      )}

      {imageUrl ? (
        <img
          className="tile-cover"
          src={imageUrl}
          alt={`Cover of ${title}`}
          loading="lazy"
          onError={(e) => {
            e.target.style.display = "none";
            e.target.nextElementSibling.style.display = "flex";
          }}
        />
      ) : null}

      <div
        className="tile-initial"
        style={imageUrl ? { display: "none" } : {}}
      >
        {title.charAt(0).toUpperCase()}
      </div>

      <div className="tile-content">
        <div className="tile-title">{title}</div>

        <div className="tile-meta">
          {book.Author_Editor || "Unknown"} • {book.Year || "N/A"}
        </div>

        {description && (
          <div className="tile-description">
            {description.length > 100 ? `${description.substring(0, 100)}...` : description}
          </div>
        )}
      </div>
    </div>
  );
}
