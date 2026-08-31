#!/usr/bin/env bash
# Pre-migration AWS inventory. Read-only: describe/list/get only.
#
#   ./aws_infra_inventory.sh [output-dir]
#
# Answers the questions that have to be settled before moving the core tier
# onto ECS:
#   - Is EvalAI-Fargate-ALB actually dead, or does traffic still reach it?
#   - Can Fargate tasks join the existing prod target group, or is it
#     target-type "instance" and therefore off limits?
#   - Which subnets exist per AZ, and which are public vs private?
#   - How many Elastic IPs are unattached and billing for nothing?

set -uo pipefail

OUT="${1:-/tmp/aws-inventory-$(date +%Y%m%d-%H%M%S)}"
MAIN_VPC="${MAIN_VPC:-vpc-a1c127c7}"
LEGACY_VPC="${LEGACY_VPC:-vpc-e38d7599}"
export AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-1}"

mkdir -p "$OUT"

CW_START="$(python3 -c 'import datetime;print((datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ"))')"
CW_END="$(python3 -c 'import datetime;print(datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))')"

run() {
    local name="$1"; shift
    printf '  %-30s' "$name"
    if "$@" >"$OUT/$name.json" 2>"$OUT/$name.err"; then
        printf 'ok\n'; rm -f "$OUT/$name.err"
    else
        printf '%s\n' "$(head -c 80 "$OUT/$name.err" | tr '\n' ' ')"
        [[ -s "$OUT/$name.json" ]] || rm -f "$OUT/$name.json"
    fi
}

echo "Output: $OUT"
echo
echo "Load balancers and target groups"
run load-balancers   aws elbv2 describe-load-balancers
run target-groups    aws elbv2 describe-target-groups

echo
echo "Networking"
run subnets-main     aws ec2 describe-subnets --filters "Name=vpc-id,Values=$MAIN_VPC"
run subnets-legacy   aws ec2 describe-subnets --filters "Name=vpc-id,Values=$LEGACY_VPC"
run route-tables     aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$MAIN_VPC"
run vpc-endpoints    aws ec2 describe-vpc-endpoints
run nat-gateways     aws ec2 describe-nat-gateways
run elastic-ips      aws ec2 describe-addresses

echo
echo "ECS"
run ecs-clusters     aws ecs list-clusters

echo
echo "Per-target-group health and 30d ALB request counts"

python3 - "$OUT" "$CW_START" "$CW_END" "$MAIN_VPC" "$LEGACY_VPC" <<'PY'
import subprocess, json, os, sys

out, cw_start, cw_end, main_vpc, legacy_vpc = sys.argv[1:6]

def aws(*args):
    proc = subprocess.run(["aws"] + list(args) + ["--output", "json"],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        return None
    try:
        return json.loads(proc.stdout or "{}")
    except ValueError:
        return None

def load(name):
    path = os.path.join(out, name + ".json")
    if not os.path.exists(path):
        return None
    try:
        with open(path) as handle:
            return json.load(handle)
    except (ValueError, OSError):
        return None

def failed(name):
    """A failed call and an empty result are indistinguishable once the JSON
    is gone. Reporting '0 subnets' when the query never ran invents a finding
    that leads to the opposite conclusion from the truth."""
    return os.path.exists(os.path.join(out, name + ".err"))

lbs = (load("load-balancers") or {}).get("LoadBalancers", [])
tgs = (load("target-groups") or {}).get("TargetGroups", [])

health = {}
for tg in tgs:
    arn = tg["TargetGroupArn"]
    doc = aws("elbv2", "describe-target-health", "--target-group-arn", arn)
    health[arn] = (doc or {}).get("TargetHealthDescriptions", [])
with open(os.path.join(out, "target-health.json"), "w") as handle:
    json.dump(health, handle, indent=2)

# Request count over 30 days is the decisive test for whether a load balancer
# is still serving anything. Zero requests plus zero healthy targets means it
# can be deleted; a nonzero count means something still depends on it.
requests = {}
for lb in lbs:
    arn = lb["LoadBalancerArn"]
    # CloudWatch wants the trailing portion, e.g. app/name/1234abcd.
    dim = arn.split(":loadbalancer/")[-1]
    doc = aws("cloudwatch", "get-metric-statistics",
              "--namespace", "AWS/ApplicationELB", "--metric-name", "RequestCount",
              "--dimensions", f"Name=LoadBalancer,Value={dim}",
              "--start-time", cw_start, "--end-time", cw_end,
              "--period", "86400", "--statistics", "Sum")
    pts = (doc or {}).get("Datapoints", [])
    requests[lb["LoadBalancerName"]] = sum(p.get("Sum", 0) for p in pts) if pts else (None if doc is None else 0)
with open(os.path.join(out, "alb-request-counts.json"), "w") as handle:
    json.dump(requests, handle, indent=2)

print("\n" + "=" * 68)
print("LOAD BALANCERS")
for lb in lbs:
    name = lb["LoadBalancerName"]
    azs = sorted(z["ZoneName"] for z in lb.get("AvailabilityZones", []))
    count = requests.get(name)
    label = "UNKNOWN" if count is None else f"{count:,.0f}"
    print(f"\n  {name}")
    print(f"    vpc={lb.get('VpcId')}  azs={','.join(azs)}")
    print(f"    requests (30d): {label}")
    if count == 0:
        print("    -> no traffic in 30 days")
    own = [t for t in tgs
           if lb["LoadBalancerArn"] in (t.get("LoadBalancerArns") or [])]
    if not own:
        print("    -> no target groups attached")
    for tg in own:
        h = health.get(tg["TargetGroupArn"], [])
        healthy = sum(1 for d in h if d.get("TargetHealth", {}).get("State") == "healthy")
        print(f"    TG {tg['TargetGroupName']}  type={tg.get('TargetType')} "
              f"port={tg.get('Port')} hc={tg.get('HealthCheckProtocol')}:{tg.get('HealthCheckPath')}")
        print(f"       targets: {len(h)} ({healthy} healthy)")
        if tg.get("TargetType") == "instance":
            print("       NOTE: type=instance -- Fargate tasks CANNOT join this")
            print("             target group. A new target-type=ip group is needed.")

print("\n" + "=" * 68)
print("SUBNETS")
routes = (load("route-tables") or {}).get("RouteTables", [])

def is_public(subnet_id):
    """Public when its route table (or the VPC main table) has an IGW route."""
    explicit = None
    main = None
    for rt in routes:
        assocs = rt.get("Associations", [])
        if any(a.get("SubnetId") == subnet_id for a in assocs):
            explicit = rt
        if any(a.get("Main") for a in assocs):
            main = rt
    table = explicit or main
    if table is None:
        return None
    return any(r.get("GatewayId", "").startswith("igw-") for r in table.get("Routes", []))

for label, key in (("main " + main_vpc, "subnets-main"), ("legacy " + legacy_vpc, "subnets-legacy")):
    if failed(key):
        print(f"\n  {label}: UNKNOWN (query failed - not a finding)")
        continue
    subnets = (load(key) or {}).get("Subnets", [])
    print(f"\n  {label}: {len(subnets)} subnets")
    for s in sorted(subnets, key=lambda x: (x["AvailabilityZone"], x["CidrBlock"])):
        pub = is_public(s["SubnetId"])
        kind = "public" if pub else ("private" if pub is False else "unknown")
        print(f"    {s['SubnetId']}  {s['AvailabilityZone']}  {s['CidrBlock']:<18} {kind}")
    azs = {s["AvailabilityZone"] for s in subnets}
    if key == "subnets-main":
        print(f"    -> {len(azs)} AZs covered: {', '.join(sorted(azs))}")
        if len(azs) < 2:
            print("    -> WARNING: multi-AZ services need at least 2")

print("\n" + "=" * 68)
print("ELASTIC IPS")
if failed("elastic-ips"):
    print("  UNKNOWN (query failed - not a finding)")
    addrs = []
else:
    addrs = (load("elastic-ips") or {}).get("Addresses", [])
unattached = [a for a in addrs if not a.get("AssociationId")]
print(f"  total {len(addrs)}, unattached {len(unattached)}")
print(f"  all public IPv4 bills at $0.005/hr => ~${len(addrs) * 0.005 * 730:,.2f}/mo total,")
print(f"  of which unattached waste is ~${len(unattached) * 0.005 * 730:,.2f}/mo")
for a in addrs:
    tag = "UNATTACHED" if not a.get("AssociationId") else (a.get("InstanceId") or a.get("NetworkInterfaceId") or "associated")
    print(f"    {a.get('PublicIp'):<16} {tag}")

print("\n" + "=" * 68)
print("NAT GATEWAYS")
for n in (load("nat-gateways") or {}).get("NatGateways", []):
    if n.get("State") != "available":
        continue
    print(f"  {n['NatGatewayId']}  subnet={n.get('SubnetId')}  vpc={n.get('VpcId')}")

print("\nVPC ENDPOINTS")
for e in (load("vpc-endpoints") or {}).get("VpcEndpoints", []):
    print(f"  {e.get('ServiceName')}  type={e.get('VpcEndpointType')}  vpc={e.get('VpcId')}")
PY

echo
echo "Written to $OUT"
