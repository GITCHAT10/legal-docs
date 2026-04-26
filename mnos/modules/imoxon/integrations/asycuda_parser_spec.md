# ASYCUDA Email Parser: AI Agent Specification

## 🎯 Objective
Extract structured declaration data from ASYCUDA notification emails to auto-trigger iMOXON clearance flows.

## 🧠 Agent Prompt (LLM)
```text
Role: Maldives Customs ASYCUDA Interpreter
Task: Parse incoming email text for customs declaration metadata.
Input: {email_body}

Extract the following JSON schema:
{
  "declaration_id": "string (format: MLE-DEC-XXXXX)",
  "shipment_id": "string (format: SHP-XXXXXXXX)",
  "importer_tin": "string",
  "total_duty_mvr": "number",
  "hs_codes": ["string"],
  "status": "string (e.g., ASSESSED)"
}

Rules:
1. Only extract if status is ASSESSED or REGISTERED.
2. If duty is 0, still record HS codes for eco-folio tracking.
3. Fail closed if declaration_id is missing.
```

## 🚀 Deployment Config
- **Trigger**: IMAP / SendGrid Inbound Parse Webhook.
- **Action**: POST to `/mnos/api/v1/logistics/clearance/v1/declare` (if new) or `/mnos/api/v1/finance/customs/pay-duty` (if assessed).
- **Security**: Emails must pass DKIM/SPF check before processing.
- **Audit**: Log raw email hash + extracted JSON to SHADOW.
