"""Month-to-date AWS spend by service (Cost Explorer, read-only). Printed before and after the AWS session."""

from datetime import UTC, date, datetime

import boto3

from ka.config import settings

ce = boto3.Session(profile_name=settings.aws_profile, region_name="us-east-1").client("ce")
today = datetime.now(UTC).date()
start = date(today.year, today.month, 1).isoformat()
end = (today.replace(day=today.day) if today.day > 1 else today).isoformat()
r = ce.get_cost_and_usage(
    TimePeriod={"Start": start, "End": today.isoformat()},
    Granularity="MONTHLY",
    Metrics=["UnblendedCost"],
    GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
)
rows = [
    (g["Keys"][0], float(g["Metrics"]["UnblendedCost"]["Amount"])) for g in r["ResultsByTime"][0]["Groups"]
]
rows = [x for x in rows if abs(x[1]) > 0.0001]
print(f"month-to-date ({start} → {today}): ${sum(a for _, a in rows):.4f}")
for name, amt in sorted(rows, key=lambda x: -x[1]):
    print(f"  {amt:>9.4f}  {name}")
