#!/usr/bin/env python


from raava import zoo

from gns import zclient


##### Public methods #####
def run(config):
    with zclient.get_context(config) as client:
        zoo.drop(client, True)
        zoo.init(client, True)
