[uwsgi]
log-date = %%Y%%m%%d-%%H%%M%%S

<%
    import os
    from maestro.guestutils import get_port
    http_port = get_port("http")
    gns_config = os.getenv("GNS_CONFIG")
%>
http = :${http_port}

module = gns.api:make_wsgi_app()
pyargv = --config ${gns_config}
enable-threads = yes

master = yes
no-orphans = yes
lazy = yes
workers = 4
threads = 25
reload-on-rss = 512
max-requests = 1000000
