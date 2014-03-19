FROM nikicat/gns

ADD gns.conf /etc/gns.d/

CMD sed -i "s/ZOOKEEPER_HOST/$ZOOKEEPER_PORT_2181_TCP_ADDR/" /etc/gns.d/gns.conf && gns-splitter.py -c /etc/gns.d
