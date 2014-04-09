# Base GNS image

FROM nikicat/ubuntu
MAINTAINER Devaev Maxim <mdevaev@gmail.com>

ADD . /root/gns

WORKDIR /root
CMD bash
