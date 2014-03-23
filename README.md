[![Build Status](https://travis-ci.org/yandex-sysmon/gns.svg?branch=master)](https://travis-ci.org/yandex-sysmon/gns)
##Global Notification System##

###Running services###
Some services need to be run using PyPy3, others can work from the usual Python3.
Pypy3 services:
* `gns-splitter.py`
* `gns-worker.py`
* `gns-collector.py`

Example commands to start:
```
PYTHONPATH=. python3 scripts/gns-api.py
PYTHONPATH=. pypy3 scripts/gns-splitter.py
```

###Basic API usage###
Compatibility layer with [Golem/submit.sbml](http://nda.ya.ru/3QTLzG):
```
curl --data 'info=test' http://localhost:7887/api/compat/golem/submit?object=foo&eventtype=bar&info=test&status=critical'
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


[![Bitdeli Badge](https://d2weczhvl823v0.cloudfront.net/yandex-sysmon/notify/trend.png)](https://bitdeli.com/free "Bitdeli Badge")

