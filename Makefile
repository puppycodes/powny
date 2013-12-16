all :
	true

pylint :
	pypy3 `which pylint` --rcfile=pylint.ini \
		raava \
		*.py \
		--output-format=colorized 2>&1 | less -SR

clean :
	rm -rf build gns.egg-info
	find . -type f -name '*.pyc' -delete
	find . -type d -name __pycache__ -delete

