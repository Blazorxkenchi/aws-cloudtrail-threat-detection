# ☁️ AWS CloudTrail Threat Detection (Serverless, Free Tier)

A real-time, serverless security monitoring system on AWS that ingests CloudTrail events, scores them for anomalies, and emails alerts. Built entirely on **AWS Free Tier**.

## 🧩 Architecture
```mermaid
flowchart TD
    CT[AWS CloudTrail] --> EB[Amazon EventBridge Rule]
    EB --> LI[AWS Lambda: CTIngest]
    LI --> DDB[(DynamoDB: CTEvents)]
    LI --> S3[S3: Raw JSON (30d lifecycle)]
    DDB --> LD[AWS Lambda: CTDetect (every 5 min)]
    LD --> SNS[SNS Topic: CTAlerts]
    SNS --> Email[Email Alert]


🚀 Features

Filters sensitive activity (Console logins, IAM changes) via EventBridge

CTIngest Lambda stores normalized events in DynamoDB and raw JSON in S3

CTDetect Lambda periodically scans, computes a risk score, and publishes an SNS alert

Minimal IAM; free-tier friendly (management events only; S3 lifecycle 30d)

🧰 Stack

CloudTrail • EventBridge • Lambda (Python) • DynamoDB • SNS • CloudWatch • IAM

⚙️ Deployment Cheatsheet

S3 bucket for raw: enable default SSE-S3; lifecycle expire after 30d.

DynamoDB table: CTEvents with partition key pk (String).

SNS topic: CTAlerts (add email subscription and confirm).

IAM roles

CTIngestRole → dynamodb:PutItem, s3:PutObject, logs:*

CTDetectRole → dynamodb:Scan|PutItem, sns:Publish, logs:*

Lambdas

CTIngest env: TABLE_NAME=CTEvents, RAW_BUCKET=<your-bucket>

CTDetect env: TABLE_NAME=CTEvents, SNS_TOPIC=<topic-arn>

EventBridge

Rule (pattern) → target CTIngest (see event_pattern.json)

Scheduler rate(5 minutes) → target CTDetect

🔐 Event pattern (high-value activity)

See event_pattern.json in this repo.

📧 Alert sample

Subject: Anomalous AWS activity detected
Message: ConsoleLogin from 203.0.113.10 @ 2025-11-05T12:00:00Z score=5.23

🛠 Future improvements

CloudWatch Dashboard

Isolation Forest model for scoring

DynamoDB TTL for auto cleanup

Author

Karmanya Jamwal — Built with ☕ + Python + lots of debugging.


## 3) Add the Lambda code files
- Click **Add file → Create new file**
  - **File name:** `lambda_ingest.py`
  - Paste the code below
  - **Commit changes** (message: `feat: add CTIngest lambda`)
