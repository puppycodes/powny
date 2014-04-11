FROM yandex/gns-python3:latest
MAINTAINER Devaev Maxim <mdevaev@gmail.com>

RUN apt-get -y update \
	&& DEBIAN_FRONTEND=noninteractive apt-get install \
		python3.4-dev \
		-y --force-yes \
	&& apt-get -y clean
RUN easy_install -H *.python.org uwsgi mako

ADD uwsgi.ini.mako /root/

WORKDIR /root
CMD mako-render uwsgi.ini.mako > uwsgi.ini && uwsgi --ini uwsgi.ini
