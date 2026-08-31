#!/usr/bin/env bash
# Whole-account cost audit. Read-only: describe/list/get only.
#
#   ./aws_cost_audit.sh [output-dir]
#
# Goes past the Cost Explorer totals to the things that quietly accumulate:
# every-commit container images, log groups that never expire, detached
# volumes, idle clusters. Those rarely show up as a spike -- they show up as
# a number that was always a bit higher than it should have been.
#
# Cost Explorer calls bill $0.01 each; this makes four.

set -uo pipefail

OUT="${1:-/tmp/aws-cost-$(date +%Y%m%d-%H%M%S)}"
export AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-1}"
mkdir -p "$OUT"

END="$(python3 -c 'import datetime;print(datetime.date.today().isoformat())')"
START="$(python3 -c 'import datetime;print((datetime.date.today()-datetime.timedelta(days=180)).isoformat())')"

run() {
    local name="$1"; shift
    printf '  %-30s' "$name"
    if "$@" >"$OUT/$name.json" 2>"$OUT/$name.err"; then
        printf 'ok\n'; rm -f "$OUT/$name.err"
    else
        printf '%s\n' "$(head -c 70 "$OUT/$name.err" | tr '\n' ' ')"
        [[ -s "$OUT/$name.json" ]] || rm -f "$OUT/$name.json"
    fi
}

echo "Output: $OUT"
echo "Window: $START -> $END"
echo
echo "Cost Explorer"
run cost-by-service \
    aws ce get-cost-and-usage --time-period "Start=$START,End=$END" \
        --granularity MONTHLY --metrics UnblendedCost \
        --group-by Type=DIMENSION,Key=SERVICE
run cost-ec2-other \
    aws ce get-cost-and-usage --time-period "Start=$START,End=$END" \
        --granularity MONTHLY --metrics UnblendedCost UsageQuantity \
        --filter '{"Dimensions":{"Key":"SERVICE","Values":["EC2 - Other"]}}' \
        --group-by Type=DIMENSION,Key=USAGE_TYPE
run cost-ecr \
    aws ce get-cost-and-usage --time-period "Start=$START,End=$END" \
        --granularity MONTHLY --metrics UnblendedCost UsageQuantity \
        --filter '{"Dimensions":{"Key":"SERVICE","Values":["Amazon EC2 Container Registry (ECR)"]}}' \
        --group-by Type=DIMENSION,Key=USAGE_TYPE
run cost-logs \
    aws ce get-cost-and-usage --time-period "Start=$START,End=$END" \
        --granularity MONTHLY --metrics UnblendedCost UsageQuantity \
        --filter '{"Dimensions":{"Key":"SERVICE","Values":["AmazonCloudWatch"]}}' \
        --group-by Type=DIMENSION,Key=USAGE_TYPE

echo
echo "Accumulators"
run ecr-repos        aws ecr describe-repositories
run log-groups       aws logs describe-log-groups
run ebs-volumes      aws ec2 describe-volumes
run ebs-snapshots    aws ec2 describe-snapshots --owner-ids self
run rds-instances    aws rds describe-db-instances
run rds-snapshots    aws rds describe-db-snapshots --snapshot-type manual
run eks-clusters     aws eks list-clusters
run ecs-clusters     aws ecs list-clusters
run savings-plans    aws savingsplans describe-savings-plans

echo
echo "================ SUMMARY ================"

python3 - "$OUT" <<'PY'
import json, os, sys, subprocess, collections

out = sys.argv[1]

def load(name):
    p = os.path.join(out, name + ".json")
    if not os.path.exists(p):
        return None
    try:
        with open(p) as h:
            return json.load(h)
    except (ValueError, OSError):
        return None

def failed(name):
    return os.path.exists(os.path.join(out, name + ".err"))

def unknown(name):
    """Never report absence when the query never ran -- 'zero volumes' and
    'could not list volumes' point in opposite directions."""
    try:
        with open(os.path.join(out, name + ".err")) as h:
            t = h.read()
    except OSError:
        return "UNKNOWN (query failed)"
    for m in ("AccessDenied", "NoCredentials", "UnauthorizedOperation",
              "ExpiredToken", "NoRegion", "not authorized"):
        if m in t:
            return f"UNKNOWN ({m})"
    return "UNKNOWN (query failed)"

def aws(*a):
    p = subprocess.run(["aws"] + list(a) + ["--output", "json"],
                       capture_output=True, text=True)
    if p.returncode != 0:
        return None
    try:
        return json.loads(p.stdout or "{}")
    except ValueError:
        return None

findings = []

# ---------- monthly bill by service ----------
print("MONTHLY BILL BY SERVICE (last 3 months)")
if failed("cost-by-service"):
    print(f"  {unknown('cost-by-service')}")
else:
    doc = load("cost-by-service") or {}
    periods = [p for p in doc.get("ResultsByTime", []) if p.get("Groups")]
    for period in periods[-3:]:
        rows = [(float(g["Metrics"]["UnblendedCost"]["Amount"]), g["Keys"][0])
                for g in period["Groups"]]
        total = sum(a for a, _ in rows)
        print(f"\n  {period['TimePeriod']['Start']}   total ${total:,.2f}")
        for amount, key in sorted(rows, reverse=True)[:12]:
            if amount >= 0.50:
                print(f"    {amount:9.2f}  {key}")

# ---------- ECR ----------
print("\n" + "=" * 56)
print("ECR  (images pushed per commit accumulate forever without a policy)")
if failed("ecr-repos"):
    print(f"  {unknown('ecr-repos')}")
else:
    repos = (load("ecr-repos") or {}).get("repositories", [])
    total_bytes = 0
    total_images = 0
    no_policy = []
    for repo in repos:
        name = repo["repositoryName"]
        size = 0
        count = 0
        token = None
        while True:
            args = ["ecr", "describe-images", "--repository-name", name,
                    "--max-items", "1000"]
            if token:
                args += ["--starting-token", token]
            page = aws(*args)
            if page is None:
                break
            details = page.get("imageDetails", [])
            count += len(details)
            size += sum(d.get("imageSizeInBytes", 0) for d in details)
            token = page.get("NextToken")
            if not token:
                break
        total_bytes += size
        total_images += count
        pol = aws("ecr", "get-lifecycle-policy", "--repository-name", name)
        if pol is None:
            no_policy.append(name)
        print(f"  {name:<46} {count:5d} images  {size / 1024**3:8,.1f} GiB"
              + ("  NO LIFECYCLE POLICY" if pol is None else ""))
    gb = total_bytes / 1e9
    cost = gb * 0.10
    print(f"\n  TOTAL {total_images} images, {total_bytes / 1024**3:,.1f} GiB "
          f"=> ~${cost:,.2f}/mo at $0.10/GB")
    if no_policy:
        findings.append((cost * 0.8, "ECR lifecycle policies",
                         f"{len(no_policy)} repos have no lifecycle policy; "
                         "expiring untagged and old images typically reclaims most of this"))

# ---------- CloudWatch Logs ----------
print("\n" + "=" * 56)
print("CLOUDWATCH LOGS  (groups with no retention keep data forever)")
if failed("log-groups"):
    print(f"  {unknown('log-groups')}")
else:
    groups = (load("log-groups") or {}).get("logGroups", [])
    never = [g for g in groups if not g.get("retentionInDays")]
    stored_never = sum(g.get("storedBytes", 0) for g in never)
    stored_all = sum(g.get("storedBytes", 0) for g in groups)
    print(f"  {len(groups)} log groups, {stored_all / 1024**3:,.1f} GiB stored")
    print(f"  {len(never)} with NO retention set, holding {stored_never / 1024**3:,.1f} GiB")
    cost = stored_all / 1e9 * 0.03
    print(f"  storage ~${cost:,.2f}/mo at $0.03/GB")
    for g in sorted(groups, key=lambda x: -x.get("storedBytes", 0))[:10]:
        ret = g.get("retentionInDays")
        print(f"    {g['logGroupName'][:52]:<52} {g.get('storedBytes', 0) / 1024**3:7,.2f} GiB  "
              f"{'never expires' if not ret else str(ret) + 'd'}")
    if never:
        findings.append((stored_never / 1e9 * 0.03 * 0.7, "log retention",
                         f"set retention on {len(never)} groups; 30-90 days is "
                         "usually plenty for application logs"))

# ---------- EBS ----------
print("\n" + "=" * 56)
print("EBS")
if failed("ebs-volumes"):
    print(f"  {unknown('ebs-volumes')}")
else:
    vols = (load("ebs-volumes") or {}).get("Volumes", [])
    unattached = [v for v in vols if not v.get("Attachments")]
    gp2 = [v for v in vols if v.get("VolumeType") == "gp2"]
    un_gb = sum(v.get("Size", 0) for v in unattached)
    gp2_gb = sum(v.get("Size", 0) for v in gp2)
    print(f"  {len(vols)} volumes; {len(unattached)} unattached ({un_gb} GiB)")
    print(f"  {len(gp2)} still gp2 ({gp2_gb} GiB) -- gp3 is ~20% cheaper at same or better performance")
    for v in unattached:
        print(f"    UNATTACHED {v['VolumeId']}  {v.get('Size')} GiB  {v.get('VolumeType')}")
    if unattached:
        findings.append((un_gb * 0.08, "delete unattached EBS volumes",
                         f"{len(unattached)} volumes attached to nothing"))
    if gp2:
        findings.append((gp2_gb * 0.02, "migrate gp2 to gp3",
                         "in-place modify, no downtime"))

if failed("ebs-snapshots"):
    print(f"  snapshots: {unknown('ebs-snapshots')}")
else:
    snaps = (load("ebs-snapshots") or {}).get("Snapshots", [])
    snap_gb = sum(s.get("VolumeSize", 0) for s in snaps)
    print(f"  {len(snaps)} owned snapshots, ~{snap_gb} GiB source "
          f"=> up to ${snap_gb * 0.05:,.2f}/mo (actual is delta-compressed, so lower)")

# ---------- RDS ----------
print("\n" + "=" * 56)
print("RDS")
if failed("rds-instances"):
    print(f"  {unknown('rds-instances')}")
else:
    for db in (load("rds-instances") or {}).get("DBInstances", []):
        print(f"  {db['DBInstanceIdentifier']}  {db['DBInstanceClass']}  "
              f"{db.get('AllocatedStorage')} GiB {db.get('StorageType')}  "
              f"multi-az={db.get('MultiAZ')}  backup={db.get('BackupRetentionPeriod')}d")
        if db.get("StorageType") == "gp2":
            findings.append((db.get("AllocatedStorage", 0) * 0.023, "RDS gp2 to gp3",
                             f"{db['DBInstanceIdentifier']} still on gp2"))

# ---------- EKS ----------
print("\n" + "=" * 56)
print("EKS  ($0.10/hr per cluster = ~$73/mo each, control plane only)")
if failed("eks-clusters"):
    print(f"  {unknown('eks-clusters')}")
else:
    clusters = (load("eks-clusters") or {}).get("clusters", [])
    print(f"  {len(clusters)} clusters: {', '.join(clusters) if clusters else 'none'}")
    if clusters:
        print(f"  control planes alone: ~${len(clusters) * 73:,.0f}/mo")
        findings.append((0, "review EKS clusters",
                         f"{len(clusters)} running; each is ~$73/mo before nodes. "
                         "Delete any left over from finished challenges"))

# ---------- Savings Plans ----------
print("\n" + "=" * 56)
print("SAVINGS PLANS")
if failed("savings-plans"):
    print(f"  {unknown('savings-plans')}")
else:
    plans = [p for p in (load("savings-plans") or {}).get("savingsPlans", [])
             if p.get("state") == "active"]
    print(f"  {len(plans)} active")
    if not plans:
        print("  none -- a 1-year no-upfront Compute Savings Plan is ~30% off")
        print("  Fargate and EC2 alike. Only worth committing once the steady-")
        print("  state footprint is known, so do this AFTER the migration.")

# ---------- ranked ----------
print("\n" + "=" * 56)
print("RANKED OPPORTUNITIES")
if not findings:
    print("  nothing flagged, or the queries that would flag it failed above")
for saving, title, detail in sorted(findings, key=lambda f: -f[0]):
    tag = f"~${saving:,.0f}/mo" if saving else "review"
    print(f"  {tag:>12}  {title}")
    print(f"                {detail}")
PY

echo
echo "Written to $OUT"
