from fastapi import Header, HTTPException, Depends

API_KEYS = {
    "dev-key-123": "11111111-1111-1111-1111-111111111111"
}

def get_project_id(x_api_key: str = Header(...)):
    project_id = API_KEYS.get(x_api_key)
    if not project_id:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return project_id
