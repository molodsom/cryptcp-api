FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y \
    wget \
    && rm -rf /var/lib/apt/lists/*

RUN pip install flask gunicorn

COPY packages/* /tmp/
RUN dpkg -i /tmp/lsb-cprocsp-base_5.0.13000-7_all.deb && \
    dpkg -i /tmp/lsb-cprocsp-rdr-64_5.0.13000-7_amd64.deb && \
    dpkg -i /tmp/lsb-cprocsp-kc1-64_5.0.13000-7_amd64.deb && \
    dpkg -i /tmp/lsb-cprocsp-capilite-64_5.0.13000-7_amd64.deb && \
    dpkg -i /tmp/cprocsp-pki-cades-64_2.0.15000-1_amd64.deb && \
    rm -f /tmp/*.deb

ENV PATH="${PATH}:/opt/cprocsp/bin/amd64:/opt/cprocsp/sbin/amd64"

COPY init.sh src/ /app/
WORKDIR /app

EXPOSE 80

CMD ["./init.sh"]
