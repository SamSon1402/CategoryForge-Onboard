.PHONY: install test demo serve docker
install:
	python -m pip install -e ".[dev]"
test:
	pytest -q
demo:
	python scripts/run_demo.py
serve:
	uvicorn category_forge.service:app --reload
docker:
	docker compose up --build
