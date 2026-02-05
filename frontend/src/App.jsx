import { useEffect, useMemo, useState } from 'react';

const MODES = {
  isbn: {
    label: 'ISBN Search (Exact)',
    endpoint: '/search/isbn',
    param: 'isbn',
  },
  title: {
    label: 'Title Semantic Search',
    endpoint: '/search/title',
    param: 'query',
  },
  semantic: {
    label: 'Semantic Search (Title + Description)',
    endpoint: '/search/semantic',
    param: 'query',
  },
};

const DEFAULT_WARNING =
  'No results met the default similarity threshold. The system lowered the threshold automatically.';

const escapeRegExp = (value) => value.replace(/[.*+?^${}()|[\\]\\]/g, '\\$&');

const highlightText = (text, phrases = []) => {
  if (!text) return '';
  let highlighted = text;
  phrases
    .filter((phrase) => phrase && phrase.trim().length > 0)
    .forEach((phrase) => {
      const regex = new RegExp(`(${escapeRegExp(phrase)})`, 'gi');
      highlighted = highlighted.replace(regex, '<mark>$1</mark>');
    });
  return highlighted;
};

const formatScore = (score) => (score === null || score === undefined ? '-' : score.toFixed(3));

const ModeSelector = ({ mode, onChange }) => (
  <div className="mode-selector">
    {Object.entries(MODES).map(([key, value]) => (
      <label key={key} className={`mode-option ${mode === key ? 'active' : ''}`}>
        <input
          type="radio"
          name="mode"
          value={key}
          checked={mode === key}
          onChange={() => onChange(key)}
        />
        {value.label}
      </label>
    ))}
  </div>
);

const SearchForm = ({ mode, values, setValues, onSubmit, loading }) => {
  const placeholders = {
    isbn: 'Enter ISBN (exact match)',
    title: 'Enter a title or phrase',
    semantic: 'Describe the topic you want to find',
  };

  const handleChange = (event) => {
    const { name, value } = event.target;
    setValues((prev) => ({ ...prev, [name]: value }));
  };

  return (
    <form className="search-form" onSubmit={onSubmit}>
      <div className="search-inputs">
        <input
          name="isbn"
          value={values.isbn}
          onChange={handleChange}
          placeholder={placeholders.isbn}
          disabled={mode !== 'isbn'}
        />
        <input
          name="title"
          value={values.title}
          onChange={handleChange}
          placeholder={placeholders.title}
          disabled={mode !== 'title'}
        />
        <input
          name="semantic"
          value={values.semantic}
          onChange={handleChange}
          placeholder={placeholders.semantic}
          disabled={mode !== 'semantic'}
        />
      </div>
      <button type="submit" disabled={loading}>
        {loading ? 'Searching...' : 'Search'}
      </button>
    </form>
  );
};

const ResultCard = ({ result }) => {
  const [expanded, setExpanded] = useState(false);
  const descriptionMatch = result.matches?.find((match) => match.field === 'description');
  const titleMatch = result.matches?.find((match) => match.field === 'title');
  const matchText = descriptionMatch?.text || result.match?.text || '';
  const displayTitle = result.title || result.Title;
  const displayAuthor = result.author || result.Author_Editor;
  const displayYear = result.year || result.Year;
  const displayScore = result.similarity ?? null;

  const hasDetails = Boolean(result.match || result.matches);

  return (
    <div className="result-card">
      <header>
        <div>
          <h3>{displayTitle}</h3>
          <p>
            {displayAuthor} · {displayYear || 'Year n/a'}
          </p>
        </div>
        {displayScore !== null && <div className="score">Similarity: {formatScore(displayScore)}</div>}
      </header>
      {hasDetails && (
        <button className="expand" onClick={() => setExpanded((prev) => !prev)}>
          {expanded ? 'Hide details' : 'Show details'}
        </button>
      )}
      {expanded && hasDetails && (
        <div className="details">
          {titleMatch && (
            <div>
              <h4>Title match</h4>
              <p>Score: {formatScore(titleMatch.score)}</p>
              <p>{titleMatch.text}</p>
            </div>
          )}
          {descriptionMatch && (
            <div>
              <h4>Description match</h4>
              <p>Score: {formatScore(descriptionMatch.score)}</p>
              <p
                className="highlighted"
                dangerouslySetInnerHTML={{
                  __html: highlightText(matchText, result.highlight_phrases),
                }}
              />
            </div>
          )}
          {result.match && !descriptionMatch && (
            <div>
              <h4>Matched text</h4>
              <p
                className="highlighted"
                dangerouslySetInnerHTML={{
                  __html: highlightText(result.match.text, result.highlight_phrases),
                }}
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
};

function App() {
  const [mode, setMode] = useState('isbn');
  const [values, setValues] = useState({ isbn: '', title: '', semantic: '' });
  const [results, setResults] = useState([]);
  const [threshold, setThreshold] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [modelInfo, setModelInfo] = useState(null);

  const activeValue = useMemo(() => values[mode], [values, mode]);

  useEffect(() => {
    fetch('/model-info')
      .then((response) => response.json())
      .then((data) => setModelInfo(data))
      .catch(() => setModelInfo(null));
  }, []);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setResults([]);
    setThreshold(null);

    if (!activeValue.trim()) {
      setError('Please enter a search value.');
      return;
    }

    const modeConfig = MODES[mode];
    const params = new URLSearchParams({ [modeConfig.param]: activeValue.trim() });

    setLoading(true);
    try {
      const response = await fetch(`${modeConfig.endpoint}?${params.toString()}`);
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Search failed');
      }
      const data = await response.json();
      if (mode === 'isbn') {
        setResults(data.data || []);
        setThreshold(null);
      } else {
        setResults(data.results || []);
        setThreshold(data.threshold || null);
      }
    } catch (err) {
      setError(err.message || 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <header className="hero">
        <h1>Library Book Finder</h1>
        <p>Semantic search for academic library collections with transparent similarity scores.</p>
      </header>

      <section className="search-panel">
        <ModeSelector mode={mode} onChange={setMode} />
        <SearchForm
          mode={mode}
          values={values}
          setValues={setValues}
          onSubmit={handleSubmit}
          loading={loading}
        />
        {threshold?.reduced && (
          <div className="warning">
            <strong>Threshold adjusted:</strong> {DEFAULT_WARNING} Final threshold:{' '}
            {threshold.threshold}
          </div>
        )}
        {error && <div className="error">{error}</div>}
      </section>

      <section className="results">
        <h2>Results</h2>
        {results.length === 0 && !loading ? (
          <p className="empty">No results yet.</p>
        ) : (
          results.map((result) => <ResultCard key={result.Acc_No || result.acc_no} result={result} />)
        )}
      </section>

      <section className="how-it-works">
        <h2>How Semantic Search Works</h2>
        <ul>
          <li>Title search embeds the title only.</li>
          <li>Semantic search embeds both title and description (equal weight).</li>
          <li>Descriptions are chunked into 2–3 sentence segments.</li>
          <li>Similarity is computed with cosine similarity using local embeddings.</li>
        </ul>
        {modelInfo && (
          <div className="model-info">
            <h3>Model Information</h3>
            <p>
              Model: <strong>{modelInfo.model_name}</strong>
            </p>
            <p>Vector dimension: {modelInfo.vector_dimension}</p>
            <p>Default threshold: {modelInfo.default_threshold}</p>
          </div>
        )}
      </section>
    </div>
  );
}

export default App;
