#  SQL Assistant

An AI-powered database assistant that helps developers write SQL queries,
create views, stored procedures, triggers, and understand their database
— all in plain English.

## Features
- Natural language to SQL conversion
- Support for PostgreSQL, MySQL, SQLite, SQL Server
- Direct database connection via MCP (auto schema extraction)
- Schema library — save and reuse multiple schemas
- Chat history per schema
- Plain English explanation for every query
- JWT authentication

## Tech Stack
| Layer | Technology |
|---|---|
| Frontend | HTML + CSS + JavaScript |
| Backend | FastAPI |
| AI Agent | LangGraph + LangChain |
| LLM | Groq (llama-3.3-70b) |
| Database | PostgreSQL + SQLAlchemy |
| Migrations | Alembic |

## Project Structure

sql-assistant/

├── backend/

│   ├── auth/          # JWT authentication

│   ├── agent/         # LangGraph AI agent

│   ├── schema/        # Schema management

│   ├── history/       # Chat history

│   ├── mcp/           # Database connector

│   ├── prompts/       # Prompt templates

│   ├── config.py      # Environment config

│   ├── database.py    # DB connection

│   └── main.py        # FastAPI app

├── frontend/

│   └── index.html     # Single file UI

├── alembic/           # Database migrations

├── .env.example       # Environment template

└── requirements.txt    

## Setup

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/sql-assistant.git
cd sql-assistant
```

### 2. Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment
```bash
cp .env.example .env
# Edit .env with your actual values
```

### 5. Create PostgreSQL database
```sql
CREATE DATABASE sql_assistant;
```

### 6. Run migrations
```bash
alembic upgrade head
```

### 7. Start the server
```bash
uvicorn backend.main:app --reload --port 8000
```

### 8. Open the UI
Open `frontend/index.html` in your browser.

