FROM yandex/ubuntu-pypy3

ADD requirements.txt /root/requirements.txt
RUN easy_install -H *.python.org `cat /root/requirements.txt`
RUN easy_install -H *.python.org git+git://github.com/signalfuse/maestro-ng
ADD etc/gns-maestro.d /root/gns.d
ADD . /root/gns
RUN easy_install -H *.python.org /root/gns

CMD gns $MODULE -c /root/gns.d/gns.yaml
