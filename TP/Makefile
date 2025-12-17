# Lance tous les tests
test:
	pytest -v

# Lance tous les tests sauf ceux de perf
unit_test:
	pytest -v -m "not perf"

# Lance uniquement les tests de pref
perf_test:
	pytest -v -m "perf"

# Génère le rapport de couverture
coverage:
	coverage run --source=src -m pytest
	coverage report -m

# Lance le linter
lint:
	ruff check src