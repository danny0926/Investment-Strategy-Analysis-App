# Trade Journal & Strategy KPI MVP

This repository contains a monorepo MVP for a broker-agnostic trade journal focused on Taiwan brokers and IBKR. It automates trade ingestion, KPI computation, and dashboard visualisation.

## Repository Structure

- `backend/` – FastAPI + SQLAlchemy service with Alembic migrations.
- `workers/` – APScheduler worker for daily broker pulls.
- `frontend/` – Next.js 14 app router UI with Tailwind and Recharts.
- `infra/` – Docker Compose, Postman collection, Makefile, environment templates.
- `tests/` – Backend pytest suite and Playwright smoke tests.
- `samples/` – Example CSV (`generic_tw.csv`).

## Getting Started

### Prerequisites
- Docker & Docker Compose
- Make (optional)

### Environment Variables
Copy `.env.example` to `.env` and adjust values as needed:

```bash
cp .env.example .env
```

Key variables:
- `APP_SECURITY__SECRET_KEY`
- `APP_DATABASE__URL`
- `NEXT_PUBLIC_API_BASE`

### Running with Docker

```bash
make up
```

This will:
- Start PostgreSQL, backend API (`http://localhost:8000`), frontend (`http://localhost:3000`), and worker.

To stop services:

```bash
docker compose down
```

### Local Development

```bash
# backend
cd backend
uvicorn app.main:app --reload

# frontend
cd frontend
npm install
npm run dev
```

Ensure PostgreSQL is running (via Docker or local instance).

### Database Migrations

```bash
make migrate
```

### Tests

```bash
make test
```

- Backend: `pytest --cov=app tests/backend`
- Frontend: `npx playwright test`

### Sample Data

Use the seed script to create demo data:

```bash
make seed
```

This populates a demo user, account, and 30 days of trades.

### CSV Parsers

`app/ingestors/email_csv_ingestor.py` defines a dialect registry. To add a new parser:
1. Implement a function `def parse_newbroker_rows(account_id: int, rows: Iterable[dict[str, str]]) -> list[TradeDTO]:`
2. Register it in the `DIALECTS` dictionary.
3. Update the upload endpoint to route based on broker.

### Real Broker Integrations

The Shioaji and IBKR ingestors currently provide stub data. Replace `fetch_trades` and `fetch_positions` with calls to the actual SDKs or REST APIs, retrieving credentials from `broker_connections.oauth_token_json`.

## Make Targets

- `make up` – Start Docker stack.
- `make dev` – Launch backend and frontend in watch mode.
- `make test` – Run backend and frontend tests.
- `make fmt` – Format Python and TypeScript code.
- `make migrate` – Apply Alembic migrations.
- `make seed` – Seed demo data.

## Thunder Client / Postman

Import `infra/trade-journal.postman_collection.json` to explore endpoints quickly.

## License

MIT
