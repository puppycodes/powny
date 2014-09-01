all:
	true

tox:
	pypy3 -m tox

apps:
	for app in api worker collector; do \
		echo -e "#!/usr/bin/env pypy3\nfrom powny.core.apps.$$app import run\nimport sys\nsys.exit(run())" > run-$$app.py; \
		chmod +x run-$$app.py; \
	done

clean:
	rm -rf build dist *.egg-info
	find . -type f -name '*.pyc' -delete
	find . -type d -name __pycache__ -delete

clean-all: clean
	rm -rf .tox .coverage run-*.py
