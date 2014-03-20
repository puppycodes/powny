FROM nikicat/gns

ADD gns.conf /etc/gns.d/

RUN mkdir /var/lib/gns-rules && cd /var/lib/gns-rules && git init && git remote add origin https://github.yandex-team.ru/monitoring/notify-rules
RUN mkdir /var/cache/gns-rules && ln -s /dev/null /var/cache/gns-rules/HEAD

CMD gns-fetch-rules.py -c /etc/gns.d --do-it-now
