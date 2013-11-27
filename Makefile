all :
	true

pylint :
	pypy3 `which pylint` --rcfile=pylint.ini \
		raava \
		*.py \
		--output-format=colorized 2>&1 | less -SR

clean :
	find . -name __pycache__ -delete

