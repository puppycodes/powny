all:
	true

test:
	PYTHONPATH=. LC_ALL=C pypy3 -m py.test -v --cov gns --cov-report term-missing

pylint:
	pypy3 `which pylint` --rcfile=pylint.ini \
		tests \
		gns \
		*.py \
		--output-format=colorized 2>&1 | less -SR

pypi:
	python setup.py register
	python setup.py sdist upload

clean:
	rm -f test.log
	rm -rf build dist gns.egg-info
	find . -type f -name '*.pyc' -delete
	find . -type d -name __pycache__ -delete

docker: docker-gns docker-gns-python3 docker-gns-uwsgi

docker-gns:
	docker build --rm -t gns $(DOCKER_BUILD_OPTS) .

docker-gns-python3:
	cp Dockerfile .Dockerfile.bak
	sed -i -e "s|FROM yandex/ubuntu-pypy3|FROM yandex/ubuntu-python3|g" Dockerfile
	docker build --rm -t gns-python3 $(DOCKER_BUILD_OPTS) .
	mv .Dockerfile.bak Dockerfile

docker-gns-uwsgi:
	cd uwsgi
	cp Dockerfile .Dockerfile.bak
	sed -i -e "s|FROM yandex/gns-python3|FROM gns-python3|g" Dockerfile
	docker build --rm -t gns-uwsgi $(DOCKER_BUILD_OPTS) .
	mv .Dockerfile.bak Dockerfile
