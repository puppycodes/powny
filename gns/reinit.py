#!/usr/bin/env python


from raava import zoo

from gns import service
from gns import zclient


def run(config):
    with zclient.get_context(config) as client:
        zoo.drop(client, True)
        zoo.init(client, True)
