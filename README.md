# 📜 Contract Lifecycle Management (CLM) System

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Vue.js](https://img.shields.io/badge/Frontend-Vue.js%203-4FC08D?style=for-the-badge&logo=vuedotjs&logoColor=white)](https://vuejs.org/)
[![Tailwind CSS](https://img.shields.io/badge/Styling-Tailwind%20CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![SQLite](https://img.shields.io/badge/Database-SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Docker](https://img.shields.io/badge/Deployment-Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

An intelligent, AI-powered system designed to streamline the entire lifecycle of your contracts—from initial upload and redlining to secure electronic signatures and version tracking.

---

## ✨ Key Features

The CLM system provides a comprehensive set of features for managing the lifecycle of contracts:

| | | |
|:---:|:---:|:---:|
| **📄 File Upload** <br> <img src="docs/file_upload.png" width="250"> <br> *Easily upload your contract documents.* | **🤖 Ask AI** <br> <img src="docs/ask_ai.png" width="250"> <br> *Leverage AI to ask questions about contracts.* | **📊 Knowledge Graph** <br> <img src="docs/knowledge_graph.png" width="250"> <br> *Visualize relationships and entities.* |
| **🔍 Document Comparison** <br> <img src="docs/document_comparison.png" width="250"> <br> *Compare different versions of a document.* | **🖊️ Redlining** <br> <img src="docs/redline.png" width="250"> <br> *Mark up and suggest changes.* | **🧐 Review Mode** <br> <img src="docs/review_mode.png" width="250"> <br> *Specialized mode for reviewing terms.* |
| **📝 Redline Review Mode** <br> <img src="docs/redline_review_mode.png" width="250"> <br> *Combined view for reviewing redlines.* | **🔏 Document Signing** <br> <img src="docs/document_sign.png" width="250"> <br> *Securely sign documents.* | **📜 Signed Version Tracking** <br> <img src="docs/signed_version.png" width="250"> <br> *Keep track of signed versions.* |

---

## 🏗️ Architecture

- **Backend**: [FastAPI](https://fastapi.tiangolo.com/) with **Python 3.13** and `uv` package manager.
- **Frontend**: [Vue.js 3](https://vuejs.org/) with **Vite** and **Tailwind CSS**.
- **Database**: **SQLite** (managed with **SQLAlchemy** and **Alembic**).
- **Deployment**: **Docker Compose** for seamless orchestration.

---

## 🚀 Getting Started

### Prerequisites
- [Docker](https://www.docker.com/get-started) and [Docker Compose](https://docs.docker.com/compose/install/)

### Running the Application
To start the entire system:
```bash
docker-compose up --build
```

- **Frontend**: [http://localhost:8080](http://localhost:8080)
- **Backend API**: [http://localhost:8000](http://localhost:8000)
- **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🛠️ Development

### Database Migrations
We use **Alembic** to handle database schema changes.

#### Creating a New Migration
When you modify `backend/app/models/models.py`, generate a new migration version:
1. **Enter the backend container**:
   ```bash
   docker-compose exec backend bash
   ```
2. **Generate migration**:
   ```bash
   ./generate_migration.sh "Description of changes"
   ```
3. **Exit the container**:
   ```bash
   exit
   ```
*Note: Remember to commit the new migration file in `backend/migrations/versions/`.*

#### Applying Migrations
Migrations are automatically applied on container startup. To manually apply them:
```bash
docker-compose exec backend uv run alembic upgrade head
```
