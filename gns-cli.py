#!/usr/bin/env python


import json

import gns.service
import chrpc.client


##### Public methods #####
def main():
    (config_dict, parser, argv_list) = gns.service.init(description="Low-level CLI tool for GNS API")
    parser.add_argument("--api-url", dest="api_url",       action="store",
        default="http://localhost:%d" % (config_dict[gns.service.S_API][gns.service.O_PORT]), metavar="<url>")
    parser.add_argument("--add",     dest="add_flag",      action="store_true")
    parser.add_argument("--cancel",  dest="cancel_job_id", action="store", metavar="<uuid>")
    parser.add_argument("--info",    dest="info_job_id",   action="store", metavar="<uuid>")
    parser.add_argument("--jobs",    dest="jobs_flag",     action="store_true")
    options = parser.parse_args(argv_list)

    proxy = chrpc.client.Proxy(options.api_url)

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

