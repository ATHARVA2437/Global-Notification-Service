from fastapi import FastAPI
from api.notifications import router as notifications_router

app = FastAPI(title="Global Notification Service (API)")
app.include_router(notifications_router, prefix="/api/v1/notifications")
