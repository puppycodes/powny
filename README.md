[![Build Status](https://travis-ci.org/yandex-sysmon/powny.svg?branch=master)](https://travis-ci.org/yandex-sysmon/powny)
[![Coverage Status](https://coveralls.io/repos/yandex-sysmon/powny/badge.png?branch=master)](https://coveralls.io/r/yandex-sysmon/powny?branch=master)
[![Latest Version](https://pypip.in/v/powny/badge.png)](https://pypi.python.org/pypi/powny/)
[![Dependency Status](https://gemnasium.com/yandex-sysmon/powny.svg)](https://gemnasium.com/yandex-sysmon/powny)
[![Gitter chat](https://badges.gitter.im/yandex-sysmon/powny.png)](https://gitter.im/yandex-sysmon/powny)


###Что это?###
Powny - это распределенная система обработки событий и исполнения функций по требованию. Функции пишутся на обычном Python и могут запрашивать создание контрольных точек во время работы. Таким образом, если исполнение было прервано в результате сбоя на одной из нод, другая нода продолжит выполнять функцию с последней контрольной точки.
В основе принципа работы Powny лежит использование [континулетов](http://pypy.readthedocs.org/en/latest/stackless.html#continulet) - части stackless-возможностей PyPy. Каждая задача представляется в виде континулета, который, при запросе создания контрольной точки, сериализуется и сохраняется в распределенное хранилище (сейчас это - [Apache ZooKeeper](http://zookeeper.apache.org/)). Восстановление заключается в десериализации и запуске процесса, исполняющего функцию.


###Установка для отладки###
Вам понадобятся ZooKeeper и PyPy3 с pip. Для установки Powny выполните такие команды:
```
git clone https://github.com/yandex-sysmon/powny.git
cd powny
pypy3 -m pip install --user -e
```
Powny будет установлен в отладочном режиме. Для запуска системы используйте такие команды (находясь в каталоге `powny`):
```
~/.local/bin/powny-api -l DEBUG
~/.local/bin/powny-worker -l DEBUG
~/.local/bin/powny-collector -l DEBUG
```
По-умолчанию, вам будут доступны правила из каталога `rules`.


###Использование с Docker/Dominator###
Для локального запуска в изолированной среде, вам потребуется [Docker](https://www.docker.com/) и [Dominator](https://github.com/yandex-sysmon/dominator). Для их настройки обратитесь в соответствующую документацию.
Чтобы запустить Powny внутри Dominator, установите питоновый пакет [obedient.powny](https://pypi.python.org/pypi/obedient.powny/2.1.4), соберите образа и запустите их:
```
dominator -l DEBUG shipment generate obedient.powny local > powny.local.yaml
dominator -l DEBUG -c powny.local.yaml image build
dominator -l DEBUG -c powny.local.yaml container start
```


###TODO & FIXME###
  * Контекстный логгер не пиклится, нужно удалять его объект из области видимости перед чекпоинтом.
  * Какая-то странная бага с относительным импортированием в хелперах, пока использую абсолютное:
```
File "/home/mdevaev/projects/yandex/powny/powny/helpers/email/__init__.py", line 13, in <module>
    from ...core.optconf import Option
ImportError: No module named powny.helpers.core
```
  * Индивидуальные `sys.path` и `sys.modules` для отдельных потоков не работают из-за кеширования загруженных правил. Если не кешировать - то будет медленно. Закостылял локом и общими объектами.
  * Тест для воркера: DELETE
  * Тест для push-back в процессе коллектора
  * Тест для секретных конфигов.
  * Обрезать значения опций в `-m`.
  * Баг в зукипере (см. `tests/fixtures/application.py`)?
```
[zk: localhost:2181(CONNECTED) 40] ls /07ba652f-2b95-4d28-a741-431a11b3001f/system/apps_state
[]
[zk: localhost:2181(CONNECTED) 41] delete /07ba652f-2b95-4d28-a741-431a11b3001f/system/apps_state
Node not empty: /07ba652f-2b95-4d28-a741-431a11b3001f/system/apps_state
```
