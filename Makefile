.PHONY: up dev test fmt migrate seed

up:
docker compose up --build

dev:
(cd backend && uvicorn app.main:app --reload) & (cd frontend && npm install && npm run dev)

test:
(cd backend && pytest --cov=app ../../tests/backend)
(cd frontend && npm install && npx playwright test)

fmt:
(cd backend && python -m black app)
(cd frontend && npx prettier --write .)

migrate:
(cd backend && alembic upgrade head)

seed:
python scripts/seed.py
