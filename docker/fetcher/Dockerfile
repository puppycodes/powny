FROM nikicat/gns

ADD gns.conf /etc/gns.d/
RUN git clone https://github.yandex-team.ru/monitoring/notify-rules /var/lib/gns-rules
RUN mkdir /var/cache/gns-rules && ln -s /dev/null /var/cache/gns-rules/HEAD

CMD gns-fetch-rules.py -c /etc/gns.d --do-it-now
