import { useState, useEffect, useRef } from "react";
import SearchBox from "./components/SearchBox";
import BookGrid from "./components/BookGrid";
import BookModal from "./components/BookModal";
import WarningBanner from "./components/WarningBanner";
import LoadingSkeleton from "./components/LoadingSkeleton";
import * as api from "./api";

export default function App() {
  const [results, setResults] = useState([]);
  const [randomBooks, setRandomBooks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [randomLoading, setRandomLoading] = useState(false);
  const [error, setError] = useState(null);
  const [warning, setWarning] = useState(null);
  const [selectedBook, setSelectedBook] = useState(null);
  const [searchPerformed, setSearchPerformed] = useState(false);
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState("title");
  const [engineReady, setEngineReady] = useState(null);
  const pollRef = useRef(null);

  // Poll engine status until ready
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const status = await api.getSearchStatus();
        setEngineReady(status.ready);
        if (status.ready) {
          clearInterval(pollRef.current);
        }
      } catch {
        // backend not up yet, keep polling
      }
    };
    checkStatus();
    pollRef.current = setInterval(checkStatus, 3000);
    return () => clearInterval(pollRef.current);
  }, []);

  useEffect(() => {
    loadFeaturedBooks();
  }, []);

  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      if (query.trim().length >= 2) {
        performSearch();
      } else {
        setResults([]);
        setSearchPerformed(false);
        setError(null);
        setWarning(null);
      }
    }, 300);

    return () => clearTimeout(debounceTimer);
  }, [query, mode]);

  const loadFeaturedBooks = async () => {
    setRandomLoading(true);
    try {
      // Increased to 12 to fill the screen better
      const books = await api.getRandomBooks(12);
      setRandomBooks(books);
    } catch (err) {
      console.error("Failed to load featured books", err);
    } finally {
      setRandomLoading(false);
    }
  };

  const performSearch = async () => {
    setLoading(true);
    setError(null);
    setWarning(null);
    setSearchPerformed(true);

    try {
      let data;

      if (mode === "isbn") {
        data = await api.searchISBN(query);
        setResults(data.data || []);
      } else if (mode === "title") {
        data = await api.searchTitle(query);
        if (data.threshold_reduced) {
          setWarning("Threshold was reduced to find matches — results may be less precise.");
        }
        setResults(data.results || []);
      } else {
        data = await api.searchSemantic(query);
        if (data.threshold_reduced) {
          setWarning("Threshold was reduced to find matches — results may be less precise.");
        }
        setResults(data.results || []);
      }
    } catch (err) {
      setError(err.message);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header>
        <h1>📚 BookFinder</h1>
        <p className="subtitle">University Library Enrichment System</p>
      </header>

      <main>
        {engineReady === false && (
          <div className="engine-status loading">
            <div className="spinner" />
            Search engine is warming up — browse books while it loads...
          </div>
        )}
        {engineReady === true && (
          <div className="engine-status ready">
            ✓ Search engine ready
          </div>
        )}

        <SearchBox
          onQueryChange={setQuery}
          onModeChange={setMode}
          initialMode={mode}
          initialQuery={query}
        />

        <WarningBanner message={warning} onHide={() => setWarning(null)} />

        {loading && <LoadingSkeleton count={4} />}

        {error && <div className="status error">❌ {error}</div>}

        {!loading && !error && searchPerformed && (
          <BookGrid
            title={`Search Results (${results.length})`}
            books={results}
            onSelect={setSelectedBook}
          />
        )}

        {!searchPerformed && (
          <div className="featured-section">
            <div className="section-header">
              <h2>Featured Library Books</h2>
              <button
                className="shuffle-btn"
                onClick={loadFeaturedBooks}
                disabled={randomLoading}
                title="Shuffle suggestions"
              >
                {randomLoading ? "..." : "🔄 Shuffle"}
              </button>
            </div>

            {randomLoading ? (
              <LoadingSkeleton count={4} />
            ) : randomBooks.length > 0 ? (
              <BookGrid
                books={randomBooks}
                onSelect={setSelectedBook}
              />
            ) : null}
          </div>
        )}
      </main>

      <BookModal
        book={selectedBook}
        onClose={() => setSelectedBook(null)}
      />

      <footer className="footer">
        <p>BDE Final Project • Semantic Search Powered by all-MiniLM-L6-v2</p>
      </footer>
    </div>
  );
}
