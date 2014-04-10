# Nginx frontend for GNS

FROM gns-base-image
MAINTAINER Devaev Maxim <mdevaev@gmail.com>

RUN add-apt-repository ppa:nginx/stable
RUN apt-get -y update
RUN DEBIAN_FRONTEND=noninteractive apt-get install \
        nginx-extras \
        liblua5.1-json \
    -y --force-yes
RUN apt-get -y clean

RUN cd /root && git clone https://github.com/yandex-sysmon/nginx-lua-stats.git
RUN mkdir -p /usr/local/share/lua/5.1/
RUN cp /root/nginx-lua-stats/common_stat.lua /usr/local/share/lua/5.1/
RUN cp /root/nginx-lua-stats/collect_stats.lua /usr/share/nginx/
RUN cp /root/nginx-lua-stats/show_stat.lua /usr/share/nginx/
RUN rm -rf /root/nginx-lua-stats

RUN cp /root/gns/etc/nginx.conf.in /root/nginx.conf.in
RUN rm -rf /root/gns

EXPOSE 7887
CMD sed -e "s|%%UWSGI_HOST%%|$GNS_UWSGI_GNS_UWSGI_HOST|g" /root/nginx.conf.in > /etc/nginx/nginx.conf \
    && nginx
