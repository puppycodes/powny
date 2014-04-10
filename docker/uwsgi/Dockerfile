FROM gns-base-image
MAINTAINER Devaev Maxim <mdevaev@gmail.com>

RUN add-apt-repository ppa:fkrull/deadsnakes
RUN apt-get -y update
RUN DEBIAN_FRONTEND=noninteractive apt-get install \
		python3.4 \
		python3.4-dev \
    -y --force-yes
RUN apt-get -y clean

RUN wget https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py -O - | python3.4
RUN rm *.zip
RUN easy_install-3.4 -H *.python.org `cat /root/gns/requirements.txt`
RUN easy_install-3.4 -H *.python.org /root/gns
RUN easy_install-3.4 -H *.python.org uwsgi
RUN easy_install-3.4 -H *.python.org git+https://github.com/signalfuse/maestro-ng

RUN cp /root/gns/etc/uwsgi.ini /root/
RUN cp -r /root/gns/etc/gns-maestro.d /root/gns.d
RUN rm -rf /root/gns

WORKDIR /root
EXPOSE 7886
CMD uwsgi --ini /root/uwsgi.ini
