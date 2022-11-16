FROM debian:buster-slim

RUN apt update
RUN apt -y install cron curl

COPY task.sh ./opt
COPY trigger-crontab /etc/cron.d/trigger-crontab
RUN chmod 0644 /etc/cron.d/trigger-crontab && crontab /etc/cron.d/trigger-crontab

ENTRYPOINT ["cron", "-f"]
