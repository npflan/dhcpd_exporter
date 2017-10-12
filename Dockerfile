FROM python:alpine

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./dhcpd_exporter.py", "/var/lib/dhcp/dhcpd.leases" ]