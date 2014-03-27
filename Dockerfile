FROM nikicat/ubuntu-pypy3

ADD requirements.txt /root/requirements.txt
RUN easy_install -H *.python.org `cat /root/requirements.txt`
RUN easy_install -H *.python.org git+git://github.com/signalfuse/maestro-ng
ADD maestro-run.py /root/
ADD etc/gns-maestro.d /root/gns.d
ADD . /root/gns
RUN easy_install -H *.python.org /root/gns

WORKDIR /root

CMD pypy3 /root/maestro-run.py
