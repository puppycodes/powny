#!/usr/bin/env python


from raava import application
from raava import collector
from gns import service


##### Public methods #####
def main():
    config = service.init(description="GNS Collector")[0]
    core_attrs = config[service.S_CORE]
    app_attrs = config[service.S_COLLECTOR]

    app = application.Application(
        thread_class      = collector.CollectorThread,
        workers           = app_attrs[service.O_WORKERS],
        die_after         = app_attrs[service.O_DIE_AFTER],
        quit_wait         = app_attrs[service.O_QUIT_WAIT],
        interval          = app_attrs[service.O_RECHECK],
        nodes_list        = core_attrs[service.O_ZOO_NODES],
        poll_interval     = app_attrs[service.O_POLL_INTERVAL],
        delay             = app_attrs[service.O_ACQUIRE_DELAY],
        recycled_priority = app_attrs[service.O_RECYCLED_PRIORITY],
        garbage_lifetime  = app_attrs[service.O_GARBAGE_LIFETIME],
    )
    app.run()


##### Main #####
if __name__ == "__main__":
    main()

