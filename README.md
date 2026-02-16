# 📚 BookFinder: University Library Enrichment System with Semantic Search

---

## 🚀 Project Overview

**BookFinder** is a full-stack university library enrichment and semantic search system. It transforms incomplete library metadata into an enriched, searchable database and exposes it through a modern web interface with intelligent semantic search capabilities.

### Key Features

- ✅ **Data Enrichment**: Automatically enriches book records with descriptions from external sources (OpenLibrary, Google Books)
- ✅ **Semantic Search**: Three search modes - ISBN exact match, Title semantic search, and Full semantic search (Title + Description)
- ✅ **Modern UI**: React + Vite frontend with responsive design
- ✅ **REST API**: FastAPI-based REST endpoints
- ✅ **Docker Support**: Containerized deployment
- ✅ **Cloud Deployment**: Ready for Render deployment
- 🌐 **Live Demo**: [book-finder-57jc.onrender.com](https://book-finder-57jc.onrender.com/)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           BookFinder Architecture                        │
└─────────────────────────────────────────────────────────────────────────┘

    ┌──────────────┐      ┌──────────────┐      ┌──────────────────┐
    │  Raw CSV     │      │  Enrichment  │      │   SQLite DB      │
    │  Data        │─────▶│  Pipeline    │─────▶│   (db.sqlite3)   │
    │(dau_library) │      │(ingestion.py)      │                  │
    └──────────────┘      └──────────────┘      └────────┬─────────┘
                                                         │
                                                         ▼
                        ┌──────────────────────────────────────────────┐
                        │              FastAPI Application              │
                        │                   (api.py)                    │
                        │                                               │
                        │  ┌─────────────┐  ┌─────────────────────────┐ │
                        │  │ /books      │  │ /search/* Endpoints     │ │
                        │  │ /book       │  │ - /search/isbn          │ │
                        │  │ /health     │  │ - /search/title         │ │
                        │  └─────────────┘  │ - /search/semantic     │ │
                        │                   │ - /search/raw          │ │
                        │                   └─────────────────────────┘ │
                        └──────────────────────────────────────────────┘
                                                         │
                                    ┌─────────────────────┴─────────────────────┐
                                    ▼                                           ▼
                    ┌────────────────────────┐               ┌────────────────────────┐
                    │   Embedding Pipeline   │               │   React Frontend      │
                    │  (build_embeddings.py) │               │   (Vite + React)      │
                    │                        │               │                        │
                    │  ┌──────────────────┐  │               │  ┌──────────────────┐ │
                    │  │ all-MiniLM-L6-v2 │  │               │  │ SearchBox        │ │
                    │  │ (384-dim vectors)│  │               │  │ BookGrid         │ │
                    │  └──────────────────┘  │               │  │ BookModal        │ │
                    │  ┌──────────────────┐   │               │  └──────────────────┘ │
                    │  │ vectors.npy     │   │               │                        │
                    │  │ metadata.json   │   │               │  ┌──────────────────┐ │
                    │  └──────────────────┘   │               │  │ Semantic Search  │ │
                    └─────────────────────────┘               │  │ UI Components    │ │
                                                              └────────────────────────┘
```

---

## 📁 Project Structure

```
Big-Data-Engg-main/
│
├── API/                          # FastAPI application
│   ├── __init__.py
│   ├── api.py                   # Main API server & endpoints
│   ├── models.py                # Pydantic models
│   ├── semantic_engine.py       # Semantic search engine
│   └── utils.py                 # Utility functions
│
├── Database/                     # SQLite database
│   ├── SQLite3.py               # Database initialization script
│   └── db.sqlite3              # SQLite database file
│
├── Data Gather/                 # Data enrichment pipeline
│   ├── data_exploration.ipynb  # Jupyter notebook for data exploration
│   ├── dau_library_data.csv    # Raw library data
│   └── ingestion.py            # Multi-source enrichment script
│
├── Data/                        # Processed data
│   ├── FinalDATA.csv           # Enriched dataset
│   └── dau_library_data.csv
│
├── embeddings/                   # Vector embeddings (generated)
│   ├── vectors.npy             # Embedding vectors
│   ├── metadata.json           # Metadata index
│   └── index.pkl               # Precomputed index (required for fast startup)
│
├── frontend/                     # React frontend (Vite)
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── api.js
│       ├── App.css
│       ├── styles.css
│       ├── components/
│       │   ├── BookGrid.jsx
│       │   ├── BookModal.jsx
│       │   ├── BookTile.jsx
│       │   ├── LoadingSkeleton.jsx
│       │   ├── SearchBox.jsx
│       │   └── WarningBanner.jsx
│       └── utils/
│           └── recent.js
│
├── scripts/                     # Build & utility scripts
│   ├── __init__.py
│   ├── build_embeddings.py     # Embedding generation script
│   ├── precompute_index.py     # Index precomputation
│   ├── test_compression.py
│   └── verify_engine.py
│
├── cli_helper.py               # CLI helper utilities
├── Dockerfile                   # Docker configuration
├── render.yaml                 # Render deployment config
└── requirements.txt            # Python dependencies
```

---

## 🧠 Core Components

### 1. Data Enrichment Pipeline (`Data Gather/ingestion.py`)

**Purpose:** Enrich raw library data with book descriptions from external sources.

**How it works:**
- Reads CSV file containing library book records
- Identifies records with missing descriptions
- Applies multi-stage enrichment strategy:

  1. **OpenLibrary lookup** (ISBN-based)
  2. **Google Books HTML scraping** (ISBN-based)
  3. **Google Books API fallback** (title + author)

- Rate-limited requests to avoid blocking
- Saves enriched data to `FinalDATA.csv`

**Why this approach:**
Real-world library data contains missing or malformed ISBNs. A single source is insufficient. The fallback-based approach ensures maximum coverage.

### 2. Database Layer (`Database/SQLite3.py`)

**Purpose:** Store enriched data in a relational database.

**Schema:**
```
sql
CREATE TABLE IF NOT EXISTS books (
    Acc_Date TEXT,
    Acc_No INTEGER PRIMARY KEY,
    Title TEXT,
    ISBN TEXT,
    Author_Editor TEXT,
    Edition_Volume TEXT,
    Place_Publisher TEXT,
    Year INTEGER,
    Pages TEXT,
    Class_No TEXT,
    description TEXT
);
```

**Features:**
- Primary key: `Acc_No` (Accession Number)
- Duplicate prevention with `INSERT OR IGNORE`
- All original metadata preserved

### 3. Semantic Search Engine (`API/semantic_engine.py`)

**Purpose:** Provide intelligent semantic search over book titles and descriptions.

**Technical Details:**

| Property | Value |
|----------|-------|
| Model | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector Dimension | 384 |
| Default Threshold | 0.60 |
| Min Threshold | 0.50 |
| Similarity Metric | Cosine Similarity |

**Key Features:**
- **Lazy Loading**: Model and vectors loaded on first use (not at import time)
- **Memory Optimization**: Uses memory-mapped files (mmap) for vectors (~130MB RAM saved)
- **Chunked Processing**: Processes vectors in chunks to avoid loading entire index into RAM
- **Pre-normalized Embeddings**: Fast dot-product similarity computation
- **Adaptive Threshold**: Automatically reduces threshold if no results found above default

**Search Modes:**
1. **Title Search**: Embeddings over `Title` field only
2. **Semantic Search**: Equal-weighted average of Title similarity and best Description chunk similarity

### 4. Embedding Pipeline (`scripts/build_embeddings.py`)

**Purpose:** Generate vector embeddings from database content.

**Process:**
1. Load books from SQLite database
2. Extract Title and Description fields
3. Split descriptions into 2-3 sentence chunks
4. Generate embeddings using `all-MiniLM-L6-v2`
5. Save vectors to `vectors.npy`
6. Save metadata to `metadata.json`

**Output Files:**
- `embeddings/vectors.npy` - NumPy array of shape (N, 384)
- `embeddings/metadata.json` - List of metadata objects

### 5. REST API (`API/api.py`)

**Purpose:** Expose book data and search functionality via HTTP endpoints.

**Technology Stack:**
- **Framework**: FastAPI
- **Server**: Uvicorn
- **Database**: SQLite3
- **CORS**: Enabled for all origins

### 6. Frontend (`frontend/`)

**Purpose:** User interface for searching and browsing books.

**Technology Stack:**
- **Framework**: React 18
- **Build Tool**: Vite 5
- **Styling**: CSS

**Features:**
- Three search modes (ISBN, Title, Semantic)
- Random book display
- Expandable results with similarity scores
- Threshold reduction warning banner
- Loading states with skeleton components
- Book detail modal

---

## 🌐 API Endpoints

### Health & Status

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/model-info` | Get model metadata |
| GET | `/search/status` | Get search engine status |

### Book Data

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/books` | Fetch books with available descriptions |
| GET | `/books/id/{acc_no}` | Fetch book by accession number |
| GET | `/books/random` | Fetch random books |

### Search Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/search/isbn?isbn=...` | Exact ISBN match |
| GET | `/search/title?query=...` | Title semantic search |
| GET | `/search/semantic?query=...` | Full semantic search (title + description) |
| GET | `/search/raw?query=...` | Raw similarity scores and chunks |
| GET | `/search/unified?q=...` | Unified search (auto-detect ISBN) |

### Response Examples

**`/search/semantic` Response:**
```
json
{
  "results": [
    {
      "Acc_No": 12345,
      "Title": "Introduction to Algorithms",
      "Author_Editor": "Cormen, T.H.",
      "description": "A comprehensive textbook...",
      "similarity": 0.85,
      "matches": [
        {
          "field": "description",
          "text": "A comprehensive textbook...",
          "score": 0.85
        }
      ]
    }
  ],
  "final_threshold": 0.60,
  "threshold_reduced": false
}
```

**`/model-info` Response:**
```
json
{
  "model_name": "sentence-transformers/all-MiniLM-L6-v2",
  "vector_dimension": 384,
  "default_threshold": 0.60
}
```

---

## 🛠️ Installation & Setup

### Prerequisites

- **Python**: 3.11+
- **Node.js**: 20+ (for frontend development)
- **SQLite3**: Built-in with Python

### 1. Clone & Install Python Dependencies

```
bash
# Clone the repository
git clone <repository-url>
cd Big-Data-Engg-main

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Build Embeddings & Index

```bash
# 1. Generate core embeddings (Title + Description)
python scripts/build_embeddings.py

# 2. Precompute search index (Optimizes RAM and startup speed)
python scripts/precompute_index.py
```

This will:
- Load the SQLite database
- Generate embeddings for all titles and descriptions
- Save vectors to `embeddings/vectors.npy`
- Save metadata to `embeddings/metadata.json`
- Save optimized index to `embeddings/index.pkl`

### 3. Run the API Server

```
bash
# Development
uvicorn API.api:app --reload

# Production
python -m uvicorn API.api:app --host 0.0.0.0 --port 8000
```

### 4. Access the Application

- **API Documentation**: http://localhost:8000/docs
- **Frontend**: http://localhost:8000/
- **Health Check**: http://localhost:8000/health

---

## 🐳 Docker Deployment

### Build Docker Image

```
bash
docker build -t library-book-finder .
```

### Run Container

```
bash
docker run -p 8000:8000 library-book-finder
```

### Docker Features

- **Multi-stage Build**: Optimized image size
- **Frontend Built-in**: React app served by FastAPI
- **Embeddings Pre-built**: Generated during image build
- **CPU-only**: No GPU required (smaller image)
- **Memory Optimized**: Uses mmap for vectors

---

## ☁️ Cloud Deployment (Render)

### Configuration

The project includes `render.yaml` for automatic deployment:

```
yaml
services:
  - type: web
    name: library-book-finder
    env: docker
    plan: free
    region: singapore
    numInstances: 1
    healthCheckPath: /health
    envVars:
      - key: PORT
        value: 10000
      - key: PYTHONUNBUFFERED
        value: 1
```

### Deploy Steps

1. Push code to GitHub
2. Connect repository to Render
3. Select "Docker" as the environment
4. Deploy automatically

**Live Link:** [https://book-finder-57jc.onrender.com/](https://book-finder-57jc.onrender.com/)

---

## 📊 Data Pipeline Summary

### Raw Dataset (`dau_library_data.csv`)

| Metric | Value |
|--------|-------|
| Total Records | ~36,358 |
| Columns | 21 |
| Usable Columns | ~10 |
| Description Coverage | 0% (100% missing) |

### Final Dataset (`FinalDATA.csv`)

| Metric | Value |
|--------|-------|
| Total Records | ~26,009 |
| Columns | 13 |
| Description Coverage | 100% |
| Avg Description Length | ~150 words |

### Transformation Summary

| Metric | Raw Data | Final Data |
|--------|----------|------------|
| Columns | 21 | 13 |
| Description Coverage | 0% | 100% |
| Records for Search | 0 | 26,009 |
| NLP Ready | ❌ No | ✅ Yes |

---

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 8000 | Server port |
| `BOOK_DB_PATH` | `Database/db.sqlite3` | Database file path |
| `PYTHONUNBUFFERED` | 1 | Enable unbuffered output |

### Semantic Search Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `DEFAULT_THRESHOLD` | 0.60 | Default similarity threshold |
| `MIN_THRESHOLD` | 0.50 | Minimum threshold for results |
| `THRESHOLD_STEP` | 0.05 | Threshold reduction step |
| `VECTOR_DIM` | 384 | Embedding dimension |

---

## 🧪 Testing

### Verify Engine

```
bash
python scripts/verify_engine.py
```

### Test Search

```
bash
# ISBN search
curl "http://localhost:8000/search/isbn?isbn=9780131103627"

# Title search
curl "http://localhost:8000/search/title?query=algorithms"

# Semantic search
curl "http://localhost:8000/search/semantic?query=machine learning"
```

---

## ⚠️ Limitations & Future Improvements

### Current Limitations

1. **Search Reliability**: External descriptions may vary in quality
2. **Speed**: Scraping is slower than paid APIs
3. **Read-Only API**: No POST/PUT endpoints
4. **Source Attribution**: Description source not stored
5. **Sync Execution**: Pipeline is synchronous
6. **Single Instance**: No horizontal scaling

### Future Improvements

1. Add caching layer (Redis)
2. Implement async enrichment pipeline
3. Add user authentication
4. Store description source for attribution
5. Add book recommendations
6. Implement faceted search
7. Add user ratings/reviews

---

## 📚 Technologies Used

### Backend
- **Python 3.11+**: Programming language
- **FastAPI**: Web framework
- **Uvicorn**: ASGI server
- **SQLite3**: Database
- **Pandas**: Data processing
- **Requests**: HTTP client
- **BeautifulSoup4**: Web scraping
- **sentence-transformers**: Embedding model
- **NumPy**: Numerical computing

### Frontend
- **React 18**: UI framework
- **Vite**: Build tool
- **CSS**: Styling

### DevOps
- **Docker**: Containerization
- **Render**: Cloud deployment

---

## 🎓 Learning Outcomes

This project demonstrates:

- ✅ ETL pipeline design and implementation
- ✅ Multi-source data enrichment strategies
- ✅ Vector embeddings and semantic search
- ✅ REST API development with FastAPI
- ✅ React frontend development
- ✅ Database design with SQLite
- ✅ Docker containerization
- ✅ Cloud deployment
- ✅ Memory optimization techniques
- ✅ Code modularity and separation of concerns

---

## 📄 License

This project is for educational purposes.

---

## 🙏 Acknowledgments

- [OpenLibrary](https://openlibrary.org/) - Book metadata
- [Google Books](https://books.google.com/) - Book descriptions
- [Hugging Face](https://huggingface.co/) - Sentence transformers model

---

## 🚀 Quick Start

```
bash
# Complete setup in 5 minutes

# 1. Install dependencies
pip install -r requirements.txt

# 2. Build embeddings
python scripts/build_embeddings.py

# 3. Run server
uvicorn API.api:app --reload

# 4. Open browser
# Visit http://localhost:8000/
```

---

*Built with ❤️ for Big Data Engineering Course*
