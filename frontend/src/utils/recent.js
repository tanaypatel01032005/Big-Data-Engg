const KEY = "recent_books";
const MAX_RECENT = 5;

/**
 * Get recently viewed books from localStorage
 */
export function getRecentBooks() {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return [];
    return JSON.parse(raw);
  } catch {
    return [];
  }
}

/**
 * Add a book to recently viewed list
 * - newest first
 * - unique by Acc_No / acc_no
 * - capped at MAX_RECENT
 */
export function addRecentBook(book) {
  if (!book) return;

  const acc =
    book.acc_no ??
    book.Acc_No ??
    null;

  if (!acc) return;

  const current = getRecentBooks();

  const filtered = current.filter(
    (b) =>
      (b.acc_no ?? b.Acc_No) !== acc
  );

  const updated = [
    book,
    ...filtered
  ].slice(0, MAX_RECENT);

  try {
    localStorage.setItem(
      KEY,
      JSON.stringify(updated)
    );
  } catch {
    /* ignore quota errors */
  }
}
