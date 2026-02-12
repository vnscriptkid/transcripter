be:
	cd backend && \
	source venv/bin/activate && \
	uvicorn app.main:app --reload --port 8000

fe:
	cd frontend && npm run dev