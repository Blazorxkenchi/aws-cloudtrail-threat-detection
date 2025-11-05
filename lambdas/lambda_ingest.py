# lambdas/lambda_ingest.py
import os, json, time, uuid, boto3

dynamodb = boto3.resource("dynamodb")
s3 = boto3.client("s3")

TABLE = os.environ["TABLE_NAME"]   # CTEvents
BUCKET = os.environ["RAW_BUCKET"]  # your S3 bucket

def normalize(ct):
    uid = ct.get("userIdentity") or {}
    add = ct.get("additionalEventData") or {}
    return {
        "pk": str(uuid.uuid4()),
        "eventTime": ct.get("eventTime"),
        "eventName": ct.get("eventName"),
        "sourceIP": ct.get("sourceIPAddress"),
        "userAgent": ct.get("userAgent"),
        "userType": uid.get("type"),
        "mfaUsed": add.get("MFAUsed"),
        "isRoot": 1 if uid.get("type") == "Root" else 0,
        "errorCode": ct.get("errorCode"),
        "awsRegion": ct.get("awsRegion"),
        "scored": 0,
        "score": None
    }

def handler(event, context):
    table = dynamodb.Table(TABLE)
    details = []

    # EventBridge -> Lambda (detail)
    if isinstance(event, dict) and "detail" in event:
        details = [event["detail"]]
    elif isinstance(event, dict) and "Records" in event:
        for rec in event["Records"]:
            if "detail" in rec:
                details.append(rec["detail"])
    else:
        details = [event] if isinstance(event, dict) else []

    stored = 0
    for d in details:
        if not isinstance(d, dict):
            continue
        # keep a raw copy in S3
        key = f"cloudtrail/{int(time.time()*1000)}.json"
        s3.put_object(Bucket=BUCKET, Key=key, Body=json.dumps(d).encode())

        # write normalized row to DynamoDB
        table.put_item(Item=normalize(d))
        stored += 1

    return {"stored": stored}
