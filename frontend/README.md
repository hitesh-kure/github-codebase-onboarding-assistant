# GitHub Codebase Onboarding Assistant

An AI-powered application that helps developers understand unfamiliar GitHub repositories. Users can register a GitHub repository, let the application clone and index its source code, and ask questions about its implementation.

The assistant searches relevant code and can retrieve GitHub information such as issues, pull requests, and commits.

## Features

- **GitHub Repository Integration:** Register GitHub repository URLs and clone repositories automatically.
- **Code Indexing:** Read source files, split them into manageable chunks, generate embeddings, and store them in ChromaDB.
- **Semantic Code Search:** Retrieve code sections relevant to a user's question.
- **AI-Powered Answers:** Generate answers using locally running Ollama models.
- **Source References:** Return relevant file paths and line numbers with answers.
- **GitHub Information:** Retrieve repository issues, pull requests, and commits.
- **Streaming Responses:** Provide status updates through Server-Sent Events (SSE).
- **Repository Management:** Register, list, view, and delete repositories.

## Technology Stack

| Component | Technologies |
|---|---|
| Frontend | React, Vite, Tailwind CSS |
| Backend | Python, FastAPI |
| Database | SQLite, SQLAlchemy, aiosqlite |
| AI Agent | LangChain, LangGraph |
| Language Models | Ollama |
| Embeddings | Ollama embedding model |
| Vector Database | ChromaDB |
| Git Integration | GitPython |
| GitHub API | HTTPX |

## Project Structure

```text
github-codebase-onboarding-assistant/
│
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   └── repository_agent.py
│   │   │
│   │   ├── api/
│   │   │   └── repositories.py
│   │   │
│   │   ├── core/
│   │   │   └── database.py
│   │   │
│   │   ├── models/
│   │   │   └── repository.py
│   │   │
│   │   └── services/
│   │       ├── chunking_service.py
│   │       ├── embedding_service.py
│   │       ├── file_service.py
│   │       ├── github_api_service.py
│   │       ├── github_service.py
│   │       ├── indexing_service.py
│   │       ├── search_service.py
│   │       ├── security_service.py
│   │       └── vector_service.py
│   │
│   ├── main.py
│   ├── requirements.txt
│   ├── test_github_api.py
│   └── test_security.py
│
└── frontend/
    ├── src/
    │   ├── assets/
    │   │   └── hero.png
    │   ├── App.jsx
    │   ├── App.css
    │   ├── index.css
    │   └── main.jsx
    │
    ├── index.html
    ├── package.json
    ├── package-lock.json
    └── vite.config.js
```

## Prerequisites

Install the following before running the application:

- Python 3.10 or later
- Node.js and npm
- Ollama
- Git

The application uses local Ollama models. Download the required models:

```powershell
ollama pull nomic-embed-text
ollama pull qwen2.5:1.5b
```

Make sure Ollama is running before starting the application.

## Installation and Setup

### 1. Clone or obtain the project

Open a terminal in the project directory.

### 2. Backend setup

Open PowerShell:

```powershell
cd backend
```

Create a virtual environment:

```powershell
python -m venv venv
```

Activate it:

```powershell
.\venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Start the FastAPI backend:

```powershell
python -m uvicorn main:app --reload
```

Backend URL:

```text
http://127.0.0.1:8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

The SQLite database tables are created automatically when the backend starts.

### 3. Frontend setup

Open a second terminal in the project directory:

```powershell
cd frontend
```

Install dependencies:

```powershell
npm install
```

Start the frontend:

```powershell
npm run dev
```

Open the local URL displayed by Vite in your browser.

## How the Application Works

1. The user submits a GitHub repository URL through the frontend.
2. The backend validates the URL and registers the repository in SQLite.
3. A background task clones the repository.
4. The application processes supported source files and splits their contents into smaller code chunks.
5. Ollama generates embeddings for the code chunks.
6. ChromaDB stores the embeddings for semantic retrieval.
7. The repository status is updated when indexing is complete.
8. The user submits a question about the repository.
9. The application searches relevant code or retrieves GitHub information, depending on the question.
10. The AI agent generates an answer and returns relevant source references.

## API Endpoints

Base URL:

```text
http://127.0.0.1:8000
```

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Check backend status |
| POST | `/api/repos` | Register a GitHub repository |
| GET | `/api/repos` | List all repositories |
| GET | `/api/repos/{repo_id}` | Get repository details |
| POST | `/api/repos/{repo_id}/chat` | Ask a question about a repository |
| POST | `/api/repos/{repo_id}/chat/stream` | Ask a question with streaming status updates |
| DELETE | `/api/repos/{repo_id}` | Delete a repository and its associated data |

### Example: Register a Repository

**POST** `/api/repos`

Request body:

```json
{
  "url": "https://github.com/owner/repository"
}
```

The backend registers the repository and starts cloning it in the background.

### Example: Ask a Question

**POST** `/api/repos/{repo_id}/chat`

Request body:

```json
{
  "question": "Explain how authentication works in this project",
  "limit": 5
}
```

The response includes the repository name, question, selected tool, generated answer, and source references.

## Database and Storage

- **SQLite:** Stores repository information and processing status.
- **ChromaDB:** Stores vector embeddings for semantic code search.
- **Repository folders:** Store cloned GitHub repositories locally.

The SQLite database is created as `codebase_assistant.db` relative to the backend working directory.

## Limitations

- Repository processing and answer generation depend on the availability of the local Ollama models.
- Answer accuracy depends on the quality and relevance of the retrieved code and GitHub information.
- Generated explanations may not always capture the complete application logic.
- The current application supports registering and deleting repositories; it does not provide repository editing through PUT or PATCH endpoints.

## Future Improvements

- Improve answer accuracy and source-grounded responses.
- Add support for more repository languages and file formats.
- Improve agent tool selection and reasoning.
- Add conversation history and follow-up question support.
- Improve indexing performance for large repositories.

---

**Project:** GitHub Codebase Onboarding Assistant  
**Purpose:** Help developers understand and explore unfamiliar GitHub codebases using AI-assisted code search and explanations.