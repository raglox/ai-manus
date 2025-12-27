from fastapi import FastAPI
import uvicorn
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Manus Test Backend")

@app.get("/")
async def root():
    return {"message": "Manus AI Backend - Test Version", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "manus-backend-test"}

if __name__ == "__main__":
    logger.info("Starting Manus Test Backend on port 8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
