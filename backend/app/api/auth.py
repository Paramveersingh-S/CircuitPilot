import os
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
import httpx 
from app.agent.session import SessionManager


# 1. Load the vault

load_dotenv()



# 2. Initialize the FastAPI router
router = APIRouter()
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")

# 3. Fetch the specific key

# 4. The Login Gateway Endpoint
@router.get("/login")

async def login_with_github():
    github_auth_url = f"https://github.com/login/oauth/authorize?client_id={GITHUB_CLIENT_ID}&scope=read:user"
    return RedirectResponse(url=github_auth_url)

@router.get("/callback")
async def get_callback(code:str):
    async with httpx.AsyncClient() as client:
        token_res = await client.post("https://github.com/login/oauth/access_token",  
                    data ={"client_id":GITHUB_CLIENT_ID,
                            "client_secret" :GITHUB_CLIENT_SECRET,
                        "code":code}, headers={"Accept": "application/json"})
        data = token_res.json()

        if "access_token" not in data:
            raise HTTPException(
                status_code=400,
                detail=data.get("error_description", "GitHub login failed"),
            )

        access_token = data["access_token"]
        headers={
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json",
}
        user = await client.get("https://api.github.com/user", headers=headers)
        if user.status_code != 200:
            raise HTTPException(status_code=502, detail="Could not fetch GitHub profile")

        github_id = str(user.json()["id"])
        session_manager = SessionManager()
        session_id = session_manager.create_session(github_id)
        return {
            "message": "Login successful!", 
            "github_id": github_id, 
            "session_id": session_id
        }


    