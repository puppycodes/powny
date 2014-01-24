#!/usr/bin/env python


from raava.apps.collector import Collector
from gns import service


##### Public methods #####
def main():
    config_dict = service.init(description="GNS Collector")[0]
    core_dict = config_dict[service.S_CORE]
    app_dict = config_dict[service.S_COLLECTOR]

    app = Collector(
        workers           = app_dict[service.O_WORKERS],
        die_after         = app_dict[service.O_DIE_AFTER],
        quit_wait         = app_dict[service.O_QUIT_WAIT],
        interval          = app_dict[service.O_RECHECK],
        host_list         = core_dict[service.O_ZOO_NODES],
        poll_interval     = app_dict[service.O_POLL_INTERVAL],
        delay             = app_dict[service.O_ACQUIRE_DELAY],
        recycled_priority = app_dict[service.O_RECYCLED_PRIORITY],
        garbage_lifetime  = app_dict[service.O_GARBAGE_LIFETIME],
    )
    app.run()


##### Main #####
if __name__ == "__main__":
    main()

