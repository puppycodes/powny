# Base GNS image

FROM yandex/ubuntu-pypy3:latest
MAINTAINER Devaev Maxim <mdevaev@gmail.com>

# XXX: OSError: Cannot load library
# /opt/pypy3/lib_pypy/_tkinter/__pycache__/_cffi__gd85ebb05xcf53ad51.pypy-23.so:
# libtcl8.5.so.0: cannot open shared object file: No such file or directory
RUN apt-get -y update
RUN DEBIAN_FRONTEND=noninteractive apt-get install \
		tk8.5 \
		libtclcl1 \
	-y --force-yes
RUN apt-get -y clean

ADD . /root/gns

RUN easy_install -H *.python.org `cat /root/gns/requirements.txt`
RUN easy_install -H *.python.org git+git://github.com/signalfuse/maestro-ng
RUN easy_install -H *.python.org /root/gns
RUN cp -r /root/gns/etc/gns-maestro.d /root/gns.d
RUN rm -rf /root/gns

EXPOSE 7886

CMD gns $GNS_MODULE -c $GNS_CONFIG
