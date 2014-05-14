[![Build Status](https://travis-ci.org/yandex-sysmon/gns.svg?branch=master)](https://travis-ci.org/yandex-sysmon/gns)
[![Coverage Status](https://coveralls.io/repos/yandex-sysmon/gns/badge.png?branch=master)](https://coveralls.io/r/yandex-sysmon/gns?branch=master)
[![Docker Repository on Quay.io](https://quay.io/repository/yandexsysmon/gns/status "Docker Repository on Quay.io")](https://quay.io/repository/yandexsysmon/gns)
[![Latest Version](https://pypip.in/v/gns/badge.png)](https://pypi.python.org/pypi/gns/)
[![Dependency Status](https://gemnasium.com/yandex-sysmon/gns.svg)](https://gemnasium.com/yandex-sysmon/gns)
[![Gitter chat](https://badges.gitter.im/yandex-sysmon/gns.png)](https://gitter.im/yandex-sysmon/gns)


##Global Notification System##


###Quick start###
To try GNS, you need to install Python 2 and [Docker](http://docker.io) from your repositories.
Docker must be running on the local socket and a special network interface:
```
sudo ip addr add 172.18.43.1/24 dev lo label lo:1
docker -d -H unix:///var/run/docker.sock -H tcp://172.18.43.1:4243
```
For configuration management, we use [Maestro-NG](https://github.com/signalfuse/maestro-ng).
You can install it from GitHub and register in the $PATH:
```
python2  -m pip install --user --upgrade git+https://github.com/signalfuse/maestro-ng.git
export PATH=$PATH:~/.local/bin
```
Next, you can clone GNS from GitHub:
```
git clone https://github.com/yandex-sysmon/gns.git
cd gns
```
Run the maestro configuration. This command can take a long time, it needs to download several images:
```
./maestro/run local reinit start
./maestro/run local reinit stop
./maestro/run local dev start
```
You can change part of the configuration parameters using environment variables. For example, you should use your repository with the rules (variable `REPO_URL`). List of all parameters can be found in YAML-files in directory `./maestro`. See file `./maestro/common.yaml` for example.


###Basic API usage###
Compatibility layer with [Golem/submit.sbml](http://nda.ya.ru/3QTLzG):
```
curl --data 'info=test' 'http://localhost:7887/api/compat/golem/submit?object=foo&eventtype=bar&info=test&status=critical'
```

Native pushing of event:
```
curl -H 'Content-Type: application/json' --data '{"host":"foo", "service":"bar", "status":"CRIT", "description":"test"}' http://localhost:7887/api/rest/v1/jobs
```
Dropping the event:
```
curl -X DELETE http://localhost:7887/api/rest/v1/jobs/<UUID>
```
Getting the information about the event:
```
curl http://localhost:7887/api/rest/v1/jobs/<UUID>
```

###Build your own image###
To build and run your locally changed GNS, you can use these following commands:
```
make docker
export DOCKER_GNS_IMAGE=gns:latest
export DOCKER_GNS_API_IMAGE=gns:latest
./maestro/run local dev start
```

###Testing###
To test your must have installed and configured ZooKeeper.
Intall PyPy3 and dependencies:
```
wget https://bootstrap.pypa.io/ez_setup.py -O - | pypy3 - --user
~/.local/bin/easy_install -H *.python.org `cat requirements.txt test_requirements.txt` pylint
```
Linting:
```
make pylint
```
Testing:
```
make test
```
Also, this project uses [Travis-Ci](https://travis-ci.org/yandex-sysmon/gns).
