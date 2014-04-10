# PyPy3-based GNS services

FROM gns-base-image

RUN apt-add-repository 'deb http://nikicat.github.io/pypy3-repo ./'
RUN apt-get -y update
RUN DEBIAN_FRONTEND=noninteractive apt-get install pypy3 -y --force-yes

# Install setuptools for PyPy3
ENV PYTHONPATH /usr/lib/pypy3/site-packages
RUN mkdir $PYTHONPATH
RUN curl https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py | pypy3
RUN rm *.zip

ENV HOME /root
ENV PATH $PATH:/usr/lib/pypy3/bin

# Install GNS
RUN easy_install -H *.python.org `cat /root/gns/requirements.txt`
RUN easy_install -H *.python.org git+git://github.com/signalfuse/maestro-ng
RUN easy_install -H *.python.org /root/gns
RUN cp -r /root/gns/etc/gns-maestro.d /root/gns.d
RUN rm -rf /root/gns

CMD gns $MODULE -c $GNS_CONFIG
