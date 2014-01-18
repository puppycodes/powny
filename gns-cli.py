#!/usr/bin/env pypy3


import json

import ulib.optconf

import gns.const
import gns.service
import gns.grpc


##### Public methods #####
def main():
    parser = ulib.optconf.OptionsConfig(
        gns.service.ALL_OPTIONS,
        gns.const.CONFIG_FILE,
    )
    parser.add_arguments(
        gns.service.ARG_LOG_FILE,
        gns.service.ARG_LOG_LEVEL,
        gns.service.ARG_LOG_FORMAT,
        gns.service.ARG_ZOO_NODES,
    )
    parser.add_raw_argument("--api-url", dest="api_url",       action="store", default="http://localhost:8080", metavar="<url>")
    parser.add_raw_argument("--add",     dest="add_flag",      action="store_true")
    parser.add_raw_argument("--cancel",  dest="cancel_job_id", action="store", metavar="<uuid>")
    parser.add_raw_argument("--info",    dest="info_job_id",   action="store", metavar="<uuid>")
    parser.add_raw_argument("--jobs",    dest="jobs_flag",     action="store_true")
    options = parser.sync(("main", "rcli"))[0]

    gns.service.init_logging(options)
    proxy = gns.grpc.Proxy(options.api_url)

    if options.add_flag:
        method = ( lambda: proxy.api.v1.events.add(**json.loads(input())) )
    elif options.cancel_job_id is not None:
        method = ( lambda: proxy.api.v1.events.cancel(options.cancel_job_id) )
    elif options.info_job_id is not None:
        method = ( lambda: proxy.api.v1.events.get_info(options.info_job_id) )
    elif options.jobs_flag:
        method = proxy.api.v1.events.get_jobs
    else:
        raise RuntimeError("Required method option")
    print(json.dumps(method(), sort_keys=True, indent=4))


##### Main #####
if __name__ == "__main__":
    main()

