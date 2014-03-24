#!/usr/bin/env python


from raava import application
from raava import collector

from gns import zclient
from gns import service


##### Public methods #####
def main():
    (config, parser, argv) = service.init(description="GNS Collector")
    parser.parse_args(argv) # Process --help
    run(config)

def run(config):
    app_opts = config[service.S_COLLECTOR]
    app = application.Application(
        thread_class      = collector.CollectorThread,
        zoo_connect       = lambda: zclient.connect(config),
        workers           = app_opts[service.O_WORKERS],
        die_after         = app_opts[service.O_DIE_AFTER],
        quit_wait         = app_opts[service.O_QUIT_WAIT],
        interval          = app_opts[service.O_RECHECK],
        poll_interval     = app_opts[service.O_POLL_INTERVAL],
        delay             = app_opts[service.O_ACQUIRE_DELAY],
        recycled_priority = app_opts[service.O_RECYCLED_PRIORITY],
        garbage_lifetime  = app_opts[service.O_GARBAGE_LIFETIME],
    )
    app.run()


##### Main #####
if __name__ == "__main__":
    main()

