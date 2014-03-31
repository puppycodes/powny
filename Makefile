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

docker-image:
	docker build -t nikicat/gns-ut .
	docker push nikicat/gns-ut

maestro-test:
	REPO_DIR=/tmp/gns-rules.git REPO_URL=https://github.yandex-team.ru/monitoring/gns-rules RULES_DIR=/tmp/gns-rules ZOOKEEPER_ZOOKEEPER_CLIENT_PORT=2181 ZOOKEEPER_ZOOKEEPER_HOST=localhost PYTHONPATH=. pypy3 -m gns.cli $(MODULE) -c etc/gns-maestro.d/gns.yaml

maestro-run-dev:
	maestro -f maestro/dev.yaml stop
	mkdir -p /tmp/gns-rules{,.git}
	#ln -fs /dev/null /tmp/gns-rules/HEAD
	#[ -d /tmp/gns-rules.git ] || git clone https://github.yandex-team.ru/monitoring/gns-rules /tmp/gns-rules.git
	SHIP=local maestro -f maestro/reinit.yaml start
	maestro -f maestro/dev.yaml start
