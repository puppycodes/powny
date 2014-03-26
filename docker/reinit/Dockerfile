FROM nikicat/gns

ADD gns.yaml /etc/gns.d/

CMD sed -i "s/ZOOKEEPER_HOST/$ZOOKEEPER_PORT_2181_TCP_ADDR/" /etc/gns.d/gns.yaml && gns-reinit.py -c /etc/gns.d/gns.yaml --do-it-now
