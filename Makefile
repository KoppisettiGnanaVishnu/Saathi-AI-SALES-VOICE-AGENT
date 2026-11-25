.PHONY: setup setup-voice backend voice frontend test demo reset

setup:
	cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
	cd frontend && npm install

# Kokoro needs Python < 3.13, so the neural voice service gets its own env.
setup-voice:
	cd backend && uv venv .tts-venv --python 3.12 && \
		uv pip install --python .tts-venv/bin/python -r voice_service/requirements.txt

backend:
	cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000

voice:
	cd backend && .tts-venv/bin/uvicorn voice_service.app:app --port 8100

frontend:
	cd frontend && npm run dev

test:
	cd backend && .venv/bin/python -m pytest -q

demo:
	backend/.venv/bin/python scripts/demo_call.py

reset:
	curl -s -X POST http://localhost:8000/api/demo/reset
