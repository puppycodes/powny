#!/usr/bin/env pypy3


import raava.rules
import raava.handlers
import raava.apps.splitter
import gns.const
import gns.service
import gns.stub

def main():
    options = gns.service.parse_options(
        app_section="splitter",
        args_list=(
            gns.service.ARG_RULES_DIR,
            gns.service.ARG_RULES_HEAD,
            gns.service.ARG_QUEUE_TIMEOUT,
        ),
    )
    gns.service.init_logging(options)

    raava.rules.setup_builtins(gns.stub.MATCHER_BUILTINS_MAP)
    raava.handlers.setup_path(options[gns.service.OPTION_RULES_DIR])

    loader = raava.handlers.Loader(
        options[gns.service.OPTION_RULES_DIR],
        options[gns.service.OPTION_RULES_HEAD],
        (
            gns.stub.HANDLER.ON_EVENT,
            gns.stub.HANDLER.ON_NOTIFY,
            gns.stub.HANDLER.ON_SEND
        ),
    )
    app = raava.apps.splitter.Splitter(
        workers=options[gns.service.OPTION_WORKERS],
        die_after=options[gns.service.OPTION_DIE_AFTER],
        quit_wait=options[gns.service.OPTION_QUIT_WAIT],
        interval=options[gns.service.OPTION_INTERVAL],
        host_list=options[gns.service.OPTION_ZOO_NODES],
        loader=loader,
        queue_timeout=options[gns.service.OPTION_QUEUE_TIMEOUT],
    )
    app.run()


if __name__ == "__main__":
    main()
