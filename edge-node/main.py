from fastapi import FastAPI
import uvicorn
import os
import sys

app = FastAPI(title="BUILDX Edge Node")

@app.get("/health")
def health():
    return {"status": "ok", "service": "edge"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8006))
    if "--port" in sys.argv:
        port = int(sys.argv[sys.argv.index("--port") + 1])
    uvicorn.run(app, host="0.0.0.0", port=port)
