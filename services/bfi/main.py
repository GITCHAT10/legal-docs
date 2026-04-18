from fastapi import FastAPI
from pydantic import BaseModel
import uuid
from datetime import datetime

app = FastAPI(title="BFI Banking Adapter")

class PaymentRequest(BaseModel):
    amount: float
    currency: str
    recipient_iban: str
    reference: str

class ISO20022Response(BaseModel):
    msg_id: str
    status: str
    xml_payload: str
    timestamp: str

@app.get("/health")
async def health():
    return {"status": "ok", "service": "bfi"}

@app.post("/transfer", response_model=ISO20022Response)
async def transfer(request: PaymentRequest):
    msg_id = str(uuid.uuid4())
    # Mock ISO 20022 XML generation
    xml_payload = f"""<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pacs.008.001.07">
    <FIToFICstmrCdtTrf>
        <GrpHdr>
            <MsgId>{msg_id}</MsgId>
            <CreDtTm>{datetime.utcnow().isoformat()}</CreDtTm>
        </GrpHdr>
        <CdtTrfTxInf>
            <Amt Ccy="{request.currency}">{request.amount}</Amt>
            <CdtrAcct><Id><IBAN>{request.recipient_iban}</IBAN></Id></CdtrAcct>
        </CdtTrfTxInf>
    </FIToFICstmrCdtTrf>
</Document>"""

    return ISO20022Response(
        msg_id=msg_id,
        status="PENDING_SETTLEMENT",
        xml_payload=xml_payload,
        timestamp=datetime.utcnow().isoformat()
    )

if __name__ == "__main__":
    import uvicorn
    import sys
    port = 8000
    if "--port" in sys.argv:
        port = int(sys.argv[sys.argv.index("--port") + 1])
    uvicorn.run(app, host="0.0.0.0", port=port)
