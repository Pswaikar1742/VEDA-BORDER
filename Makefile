.PHONY: api-install api-test api-run benchmark evaluate-task03 evaluate-task04 web-install web-run test

api-install:
	python3 -m pip install -r services/api/requirements.txt

api-test:
	cd services/api && pytest -q

api-run:
	cd services/api && uvicorn app.main:app --reload

benchmark:
	python3 services/api/tools/generate_synthetic_benchmark.py

evaluate-task03:
	python3 services/api/tools/evaluate_task03.py

evaluate-task04:
	python3 services/api/tools/evaluate_task04.py

web-install:
	cd apps/web && npm install

web-run:
	cd apps/web && npm run dev

test: api-test
