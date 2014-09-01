[![Build Status](https://travis-ci.org/yandex-sysmon/gns2.svg?branch=master)](https://travis-ci.org/yandex-sysmon/gns2)
[![Coverage Status](https://coveralls.io/repos/yandex-sysmon/gns2/badge.png?branch=master)](https://coveralls.io/r/yandex-sysmon/gns2?branch=master)
[![Latest Version](https://pypip.in/v/gns2/badge.png)](https://pypi.python.org/pypi/gns2/)
[![Dependency Status](https://gemnasium.com/yandex-sysmon/gns2.svg)](https://gemnasium.com/yandex-sysmon/gns2)
[![Gitter chat](https://badges.gitter.im/yandex-sysmon/gns2.png)](https://gitter.im/yandex-sysmon/gns2)


###Debugging###
```
pip install --user -e .
~/.local/bin/powny-api
~/.local/bin/powny-worker
~/.local/bin/powny-collector
```

###TODO & FIXME###
  * Контекстный логгер не пиклится, нужно удалять его объект перед чекпоинтом из области видимости.
  * Какая-то странная хрень с относительным импортированием в хелперах, пока использую абсолютное:
```
File "/home/mdevaev/projects/yandex/gns2/powny/helpers/email/__init__.py", line 13, in <module>
    from ...core.optconf import Option
ImportError: No module named powny.helpers.core
```
  * Индивидуальные `sys.path` и `sys.modules` для отдельных потоков не работают из-за кеширования загруженных правил. Если не кешировать - то будет медленно. Закостылял локом и общими объектами.
  * Тест для воркера: DELETE
  * Тест для push-back в процессе коллектора
  * Тест для секретных конфигов.
  * Обрезать значения опций в `-m`.
  * Актуализировать докстринги в апи.
  * Баг в зукипере (см. `tests/fixtures/application.py`)?
```
[zk: localhost:2181(CONNECTED) 40] ls /07ba652f-2b95-4d28-a741-431a11b3001f/system/apps_state
[]
[zk: localhost:2181(CONNECTED) 41] delete /07ba652f-2b95-4d28-a741-431a11b3001f/system/apps_state
Node not empty: /07ba652f-2b95-4d28-a741-431a11b3001f/system/apps_state
```
