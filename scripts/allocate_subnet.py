#!/usr/bin/env python3
import argparse
import json
import ipaddress
import csv
import re
from datetime import date
from pathlib import Path

parser = argparse.ArgumentParser(description="Subnet allocator with auto subnet naming")
parser.add_argument("--region", required=True)
parser.add_argument("--size", required=True)
parser.add_argument("--pool", required=True)
parser.add_argument("--csv", required=True)
args = parser.parse_args()

candidate_pools = json.loads(args.pool)
size = int(args.size.replace('/', ''))
region = args.region
csv_file = Path(args.csv)

def read_existing_subnet_names(region):
    """Read existing subnet names from CSV and find last number for region."""
    if not csv_file.exists():
        return 0
    pattern = re.compile(rf"{region}-auto-(\d+)", re.IGNORECASE)
    last_num = 0
    with csv_file.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("Subnet Name", "")
            match = pattern.search(name)
            if match:
                num = int(match.group(1))
                if num > last_num:
                    last_num = num
    return last_num

def allocate_subnet():
    for pool in candidate_pools:
        cidr = ipaddress.ip_network(pool["CIDR Range"])
        used = pool.get("Used CIDRs", "")
        used_nets = [ipaddress.ip_network(u.strip()) for u in used.split(",") if u.strip()]
        for subnet in cidr.subnets(new_prefix=size):
            if not any(subnet.overlaps(u) for u in used_nets):
                next_id = read_existing_subnet_names(region) + 1
                subnet_name = f"{region}-auto-{next_id:03d}"
                return {
                    "region": region,
                    "allocated": str(subnet),
                    "from_pool": pool["CIDR Range"],
                    "subnet_name": subnet_name,
                    "date": str(date.today())
                }
    return {"error": "No available subnet found"}

print(json.dumps(allocate_subnet()))
