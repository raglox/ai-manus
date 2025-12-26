"""
Temporary test endpoint to debug authentication
"""
from fastapi import FastAPI, Request, Header
from typing import Optional

app = FastAPI()

@app.post("/test-auth")
async def test_auth(
    request: Request,
    authorization: Optional[str] = Header(None)
):
    headers_dict = dict(request.headers)
    
    return {
        "authorization_header": authorization,
        "all_headers": headers_dict,
        "has_authorization": "authorization" in headers_dict
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
