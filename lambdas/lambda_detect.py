# lambdas/lambda_detect.py
import os, boto3, datetime as dt
from decimal import Decimal

dynamodb = boto3.resource("dynamodb")
sns = boto3.client("sns")

TABLE = os.environ["TABLE_NAME"]   # CTEvents
TOPIC_ARN = os.environ["SNS_TOPIC"]  # arn:aws:sns:region:acct:CTAlerts
THRESHOLD = float(os.environ.get("THRESHOLD", "5.0"))

def score_batch(rows):
    feats = []
    for r in rows:
        ts = (r.get("eventTime") or "").rstrip("Z")
        try:
            hour = dt.datetime.fromisoformat(ts).hour
        except Exception:
            hour = 0
        feats.append((hour, int(r.get("isRoot", 0))))
    if not feats:
        return []

    n = len(feats)
    mean_h = sum(f[0] for f in feats) / n
    mean_r = sum(f[1] for f in feats) / n
    var_h = sum((f[0] - mean_h) ** 2 for f in feats) / n
    var_r = sum((f[1] - mean_r) ** 2 for f in feats) / n
    std_h = (var_h ** 0.5) or 1e-6
    std_r = (var_r ** 0.5) or 1e-6

    scores = []
    for h, r in feats:
        z = abs((h - mean_h) / std_h) + abs((r - mean_r) / std_r)
        scores.append(z)
    return scores

def handler(event, context):
    table = dynamodb.Table(TABLE)
    resp = table.scan(
        FilterExpression="scored = :z",
        ExpressionAttributeValues={":z": 0},
        Limit=25
    )
    items = resp.get("Items", [])
    if not items:
        return {"scored": 0, "alerts": 0}

    scores = score_batch(items)
    alerts = []
    for itm, s in zip(items, scores):
        itm["scored"] = 1
        itm["score"] = Decimal(str(s))   # DynamoDB needs Decimal, not float
        table.put_item(Item=itm)
        if s > THRESHOLD:
            alerts.append(itm)

    if alerts:
        msg = "Suspicious CloudTrail events:\n" + "\n".join(
            f"- {a.get('eventName')} from {a.get('sourceIP')} @ {a.get('eventTime')} score={float(a.get('score', 0)):.2f}"
            for a in alerts[:10]
        )
        sns.publish(TopicArn=TOPIC_ARN, Subject="Anomalous AWS activity detected", Message=msg)

    return {"scored": len(items), "alerts": len(alerts)}
