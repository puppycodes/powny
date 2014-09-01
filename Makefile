all:
	true

tox:
	pypy3 -m tox

clean:
	rm -rf build dist *.egg-info
	find . -type f -name '*.pyc' -delete
	find . -type d -name __pycache__ -delete

clean-all: clean
	rm -rf .tox .coverage
