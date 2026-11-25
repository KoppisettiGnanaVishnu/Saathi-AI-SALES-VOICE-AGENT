.PHONY: setup backend frontend test demo reset

setup:
	cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
	cd frontend && npm install

backend:
	cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

test:
	cd backend && .venv/bin/python -m pytest -q

demo:
	backend/.venv/bin/python scripts/demo_call.py

reset:
	curl -s -X POST http://localhost:8000/api/demo/reset
