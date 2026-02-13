be:
	cd backend && \
	source venv/bin/activate && \
	uvicorn app.main:app --reload --port 8000

be_install:
	cd backend && \
	source venv/bin/activate && \
	pip install -r requirements.txt

be_migrate:
	cd backend && \
	source venv/bin/activate && \
	alembic upgrade head

fe:
	cd frontend && npm run dev

pg:
	docker compose up -d postgres

# shell into the postgres container using psql
pg-shell:
	docker compose exec postgres psql -U postgres -d transcripter