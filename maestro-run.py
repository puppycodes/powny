#!/usr/bin/env python
import os
import importlib
import logging
from maestro.guestutils import *
import gns.service

config = gns.service.load_config(os.environ["CONFIG"])
config["core"]["zoo-nodes"] = get_node_list("zookeeper", ports=["client"])
config["core"]["rules-dir"] = os.environ["RULES_DIR"]
config["git"]["repo-dir"] = os.environ["REPO_DIR"]

print("using config: %s" % config)

gns.service.init_logging(config)

module = importlib.import_module("gns."+os.environ["MODULE"])
module.run(config)
