import { useState } from "react";

export default function SearchBox({ onQueryChange, onModeChange, initialMode, initialQuery }) {
  const [mode, setMode] = useState(initialMode || "title");
  const [query, setQuery] = useState(initialQuery || "");

  const handleModeChange = (newMode) => {
    setMode(newMode);
    onModeChange(newMode);
  };

  const handleQueryChange = (newQuery) => {
    setQuery(newQuery);
    onQueryChange(newQuery);
  };

  return (
    <div className="search-box">
      <div className="tabs">
        <div
          className={`tab ${mode === "title" ? "active" : ""}`}
          onClick={() => handleModeChange("title")}
        >
          Title
        </div>
        <div
          className={`tab ${mode === "isbn" ? "active" : ""}`}
          onClick={() => handleModeChange("isbn")}
        >
          ISBN
        </div>
        <div
          className={`tab ${mode === "description" ? "active" : ""}`}
          onClick={() => handleModeChange("description")}
        >
          Description
        </div>
      </div>

      <input
        className="search-input"
        placeholder={`Search by ${mode}…`}
        value={query}
        onChange={(e) => handleQueryChange(e.target.value)}
      />
    </div>
  );
}
