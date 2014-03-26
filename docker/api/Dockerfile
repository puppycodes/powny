FROM nikicat/gns

ADD gns.yaml /etc/gns.d/

EXPOSE 7887

CMD sed -i "s/ZOOKEEPER_HOST/$ZOOKEEPER_PORT_2181_TCP_ADDR/" /etc/gns.d/gns.yaml && gns-api.py -c /etc/gns.d/gns.yaml
