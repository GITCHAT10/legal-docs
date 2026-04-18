from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
import random

app = FastAPI(title="SVD Verification Engine")

class VerificationResult(BaseModel):
    verified: bool
    confidence: float
    rules_passed: list
    message: str

@app.get("/health")
async def health():
    return {"status": "ok", "service": "svd"}

@app.post("/verify", response_model=VerificationResult)
async def verify_image(item_type: str):
    # Mock vision/rules verification
    confidence = random.uniform(0.85, 0.99)
    rules = ["quantity_match", "label_legibility", "origin_authenticated"]

    return VerificationResult(
        verified=True,
        confidence=confidence,
        rules_passed=rules,
        message=f"Item {item_type} verified successfully via vision rules."
    )

if __name__ == "__main__":
    import uvicorn
    import sys
    port = 8000
    if "--port" in sys.argv:
        port = int(sys.argv[sys.argv.index("--port") + 1])
    uvicorn.run(app, host="0.0.0.0", port=port)
