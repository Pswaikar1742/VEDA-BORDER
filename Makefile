.PHONY: api-install api-test api-run benchmark evaluate-task03 evaluate-task04 fixtures evaluate-integrated web-install web-build web-run test docker-up docker-down docker-build

api-install:
	python3 -m pip install -r services/api/requirements.txt

api-test:
	python3 -m pytest -q services/api/tests

api-run:
	cd services/api && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

benchmark:
	python3 services/api/tools/generate_synthetic_benchmark.py

evaluate-task03:
	python3 services/api/tools/evaluate_task03.py

evaluate-task04:
	python3 services/api/tools/evaluate_task04.py

fixtures:
	python3 services/api/tools/generate_integrated_fixtures.py

evaluate-integrated:
	python3 services/api/tools/evaluate_integrated.py

evaluate-external:
	PYTHONPATH=services/api python3 services/api/tools/evaluate_external_benchmarks.py

web-install:
	cd apps/web && npm install

web-build:
	cd apps/web && npm run build

web-run:
	cd apps/web && npm run dev

docker-up:
	docker compose up --build

docker-down:
	docker compose down

docker-build:
	docker compose build

test: api-test evaluate-integrated

