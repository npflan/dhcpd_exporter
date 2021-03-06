from isc_dhcp_leases import Lease, IscDhcpLeases
from prometheus_client import start_http_server, Gauge
import urllib
import os
import csv
import io
from ipaddress import IPv4Network, IPv4Address

import sys
import time

if len(sys.argv) < 2:
    # Needs file argument
    print("Needs leases file argument")
    exit(-1)

# Define metrics
TOTAL_LEASES = Gauge('total_leases', 'Total amount of leases valid and invalid')
TOTAL_CURRENT = Gauge('total_current', 'Total amount of current valid leases')
USAGE_PER_SCOPE = Gauge('usage_per_scope', 'Currently in use leases per scope', ['scope'])
SIZE_PER_SCOPE = Gauge('size_per_scope', 'Size of scope', ['scope'])

dhcpd_leases = sys.argv[1]

# Instantiate and parse DHCPD leases file
leases = IscDhcpLeases(dhcpd_leases)

netbox = 'https://netbox.minserver.dk/ipam/prefixes/?status=1&parent=&family=&q=&vrf=npflan&mask_length=&export'
data = urllib.request.urlopen(netbox).read()

datafile = os.path.join(os.path.dirname(__file__), 'data.csv')
with open(datafile, 'wb+') as f:
    f.write(data)

reader = csv.reader(io.StringIO(data.decode()), delimiter=',', quotechar='|')

subnets = []

for row in reader:
    if row[7].lower() == "Access".lower() or row[7].lower() == "Wireless".lower() or row[9].lower() == "AP-MGMT".lower():
        if row[9].lower() == 'Wireless Networks'.lower():
            continue
        # Add networks to array
        subnets.append(IPv4Network(row[0]))


def generate_per_scope():
    used_ips = 0
    for network in subnets:
        for lease in leases.get():
            if lease.valid and lease.active:
                if IPv4Address(lease.ip) in network:
                    used_ips = used_ips + 1
        USAGE_PER_SCOPE.labels(network).set(used_ips)
        SIZE_PER_SCOPE.labels(network).set(network.num_addresses-2)
        used_ips = 0


TOTAL_LEASES.set_function(lambda: len(leases.get()))
TOTAL_CURRENT.set_function(lambda: len(leases.get_current().keys()))

# Start HTTP server
start_http_server(8000)

while True:
    # Instantiate and parse DHCPD leases file
    leases = IscDhcpLeases(dhcpd_leases)

    TOTAL_LEASES.set_function(lambda: len(leases.get()))
    TOTAL_CURRENT.set_function(lambda: len(leases.get_current()))

    generate_per_scope()

    time.sleep(5)