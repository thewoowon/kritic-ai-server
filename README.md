# Kritic Server - AI Response Reality Check Platform (Backend)

FastAPI backend for multi-LLM analysis platform.

## Tech Stack

- Python 3.11+
- FastAPI
- SQLAlchemy
- PostgreSQL / SQLite
- OpenAI GPT-5, Anthropic Claude, Google Gemini APIs

## Getting Started

### Prerequisites

- Python 3.11+
- Conda (optional but recommended)

### Installation

```bash
# Using conda
conda create -n kritic python=3.11
conda activate kritic

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` and set your API keys:

```env
DATABASE_URL=sqlite:///./kritic.db
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
GOOGLE_API_KEY=your_google_api_key
```

### Database Setup

```bash
# Create tables
python3 -c "from app.db.base import Base; from app.db.session import sync_engine; Base.metadata.create_all(bind=sync_engine)"
```

### Development

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API will be available at [http://localhost:8000](http://localhost:8000)

API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## Deployment to Railway

### Prerequisites

1. GitHub repository with your code
2. Railway account
3. API keys for OpenAI, Anthropic, Google

### Steps

1. Push your code to GitHub

2. Go to [Railway](https://railway.app)

3. Click "New Project" → "Deploy from GitHub repo"

4. Select your repository

5. Add a PostgreSQL database:
   - Click "New" → "Database" → "Add PostgreSQL"
   - Railway will automatically set `DATABASE_URL` environment variable

6. Configure environment variables in Railway:
   ```
   OPENAI_API_KEY=sk-...
   ANTHROPIC_API_KEY=sk-ant-...
   GOOGLE_API_KEY=...
   DEBUG=False
   BACKEND_CORS_ORIGINS=https://your-vercel-app.vercel.app
   ```

7. Deploy!

### Post-Deployment

1. Update your frontend's `NEXT_PUBLIC_API_URL` to your Railway URL
2. Database tables will be created automatically on first run

## API Endpoints

### Analysis

- `POST /api/analyze` - Create new analysis
- `GET /api/analyze/{id}` - Get analysis results
- `GET /api/analyze/history` - Get analysis history

### Credits

- `POST /api/credits/purchase` - Purchase credits
- `GET /api/credits/balance` - Get current balance
- `GET /api/credits/transactions` - Get transaction history

## Project Structure

```
app/
├── api/
│   └── v1/
│       └── endpoints/
│           ├── analyze.py
│           └── credits.py
├── core/
│   └── config.py
├── db/
│   ├── base.py
│   └── session.py
├── models/
│   ├── user.py
│   ├── analysis.py
│   └── transaction.py
├── schemas/
│   ├── analysis.py
│   └── credits.py
├── services/
│   └── analysis_service.py
└── main.py
```

## License

Proprietary
