all:
	true

test:
	PYTHONPATH=. LC_ALL=C pypy3 run-tests.py

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

docker-start:
	docker run --name gns-rules nikicat/gns-rules
	docker run --rm --name gns-fetcher nikicat/gns-fetcher
	docker run -d --name zookeeper jplock/zookeeper
	docker run -d --volumes-from gns-rules --link zookeeper:zookeeper --name gns-worker nikicat/gns-worker
	docker run -d --volumes-from gns-rules --link zookeeper:zookeeper --name gns-splitter nikicat/gns-splitter
	docker run -d --link zookeeper:zookeeper --name gns-collector nikicat/gns-collector
	docker run -d --link zookeeper:zookeeper --name gns-api nikicat/gns-api

docker-clean:
	docker rm -f gns-api || true
	docker rm -f gns-splitter || true
	docker rm -f gns-worker || true
	docker rm -f gns-collector || true
	docker rm -f zookeeper || true
	docker rm gns-rules || true

docker-image:
	docker build -t nikicat/gns-untrusted .
	docker push nikicat/gns-untrusted

maestro-test:
	ZOOKEEPER_ZOOKEEPER_CLIENT_PORT=2181 ZOOKEEPER_ZOOKEEPER_HOST=localhost MODULE=$(MODULE) PYTHONPATH=. pypy3 maestro-run.py
