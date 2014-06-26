# Base GNS image

FROM yandex/trusty-with-pypy3
MAINTAINER Devaev Maxim <mdevaev@gmail.com>

# XXX: OSError: Cannot load library
# /opt/pypy3/lib_pypy/_tkinter/__pycache__/_cffi__gd85ebb05xcf53ad51.pypy-23.so:
# libtcl8.5.so.0: cannot open shared object file: No such file or directory
RUN apt-get -y update \
	&& DEBIAN_FRONTEND=noninteractive apt-get install \
		tk \
		libtclcl1 \
		-y --force-yes \
	&& apt-get -y clean

ADD . /root/gns
RUN pip3 install -e /root/gns

VOLUME /etc/gns
VOLUME /var/lib/gns/rules

CMD trap exit TERM; gns $GNS_MODULE -c /etc/gns/gns.yaml & wait
