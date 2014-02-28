#!/usr/bin/env python


# pylint: disable=W0401,W0614
from tests.test_flow import *

import unittest
from gns import service


##### Main #####
if __name__ == "__main__":
    service.init(config_dir_path="etc/gns-test.d") # Init logging
    unittest.main()

