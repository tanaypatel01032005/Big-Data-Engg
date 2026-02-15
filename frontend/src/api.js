const BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export async function searchTitle(query) {
  const res = await fetch(
    `${BASE}/search/title?query=${encodeURIComponent(query)}`
  );
  if (!res.ok) throw new Error("Title search failed");
  return res.json();
}

export async function searchSemantic(query) {
  const res = await fetch(
    `${BASE}/search/semantic?query=${encodeURIComponent(query)}`
  );
  if (!res.ok) throw new Error("Semantic search failed");
  return res.json();
}

export async function searchISBN(isbn) {
  const res = await fetch(
    `${BASE}/search/isbn?isbn=${encodeURIComponent(isbn)}`
  );
  if (!res.ok) throw new Error("ISBN search failed");
  return res.json();
}

export async function getRandomBooks(limit = 8) {
  const res = await fetch(`${BASE}/books/random?limit=${limit}`);
  if (!res.ok) throw new Error("Failed to fetch random books");
  const json = await res.json();
  return json.data || [];
}

export async function getBookById(accNo) {
  const res = await fetch(`${BASE}/books/id/${accNo}`);
  if (!res.ok) throw new Error("Failed to fetch book");
  return res.json();
}

export async function getSearchStatus() {
  const res = await fetch(`${BASE}/search/status`);
  if (!res.ok) return { ready: false, loading: true };
  return res.json();
}
