# BUILD-USING:        docker build -t nikicat/gns-rules .
# RUN-USING:          docker run --name gns-rules nikicat/gns-rules
FROM          busybox
RUN           mkdir /var/cache/gns-rules && ln -s /dev/null /var/cache/gns-rules/HEAD
VOLUME        ["/var/cache/gns-rules"] 
CMD           ["/bin/true"]
