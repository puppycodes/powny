all:
	true

tox:
	pypy3 -m tox

pylint:
	pypy3 -m tox -e pylint

test:
	pypy3 -m tox -e unittest

pypi:
	python setup.py register
	python setup.py sdist upload

clean:
	rm -f test.log
	rm -rf build dist gns.egg-info
	find . -type f -name '*.pyc' -delete
	find . -type d -name __pycache__ -delete

clean-all: clean
	rm -rf .tox

docker: docker-gns docker-gns-python3 docker-gns-uwsgi

docker-gns:
	./docker-build.sh . yandex/ubuntu-pypy3:latest -t gns $(DOCKER_BUILD_OPTS)

docker-gns-python3:
	./docker-build.sh . yandex/ubuntu-python3:latest -t gns-python3 $(DOCKER_BUILD_OPTS)

docker-gns-uwsgi:
	./docker-build.sh uwsgi gns-python3:latest -t gns-uwsgi $(DOCKER_BUILD_OPTS)
