#!/usr/bin/env pypy3

import kazoo.exceptions

from raava import zoo

import gns

gns.init_logging()
z = zoo.connect(["localhost"])
for path in (zoo.INPUT_PATH, zoo.READY_PATH, zoo.RUNNING_PATH, zoo.CONTROL_PATH):
    try:
        z.delete(path, recursive=True)
    except kazoo.exceptions.NoNodeError:
        pass
zoo.init(z)

