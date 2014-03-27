#!/usr/bin/env python
import os
import importlib
from maestro.guestutils import *
import gns.service

config = gns.service.load_config('gns.d')
gns.service.init_logging(config)

config[gns.service.S_CORE][gns.service.O_ZOO_NODES] = get_node_list('zookeeper', ports=['client'])

module = importlib.import_module('gns.'+os.environ['MODULE'])
module.run(config)
