from fastapi import APIRouter, Depends, HTTPException
from ..schemas import SendRequest, SendResponse
from ..auth import get_project_id
from ..db import SessionLocal
import uuid
import json
from sqlalchemy import text

router = APIRouter()

@router.post("/send", response_model=SendResponse)
def send_notification(req: SendRequest, project_id: str = Depends(get_project_id)):
    db = SessionLocal()
    try:
        # Idempotency check
        if req.idempotency_key:
            sql = text("SELECT id, status FROM notifications WHERE project_id=:p AND idempotency_key=:k")
            row = db.execute(sql, {"p": project_id, "k": req.idempotency_key}).fetchone()
            if row:
                return {"id": str(row[0]), "status": row[1]}

        nid = str(uuid.uuid4())
        sql_insert = text("""
            INSERT INTO notifications (id, project_id, type, channel, recipient, payload, template_id, status, idempotency_key)
            VALUES (:id, :project_id, :type, :channel, :recipient, :payload, :template_id, :status, :idempotency_key)
        """)
        db.execute(sql_insert, {
            "id": nid,
            "project_id": project_id,
            "type": "template" if req.template_id else "raw",
            "channel": req.channel,
            "recipient": req.recipient,
            "payload": json.dumps(req.payload or {}),
            "template_id": req.template_id,
            "status": "queued",
            "idempotency_key": req.idempotency_key
        })
        db.commit()

        return {"id": nid, "status": "queued"}
    finally:
        db.close()

@router.get("/{notification_id}")
def get_notification(notification_id: str, project_id: str = Depends(get_project_id)):
    db = SessionLocal()
    try:
        sql = text("SELECT id, project_id, channel, recipient, payload, status, created_at FROM notifications WHERE id=:id")
        row = db.execute(sql, {"id": notification_id}).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Not found")
        if str(row[1]) != project_id:
            raise HTTPException(status_code=403, detail="Forbidden")
        return {
            "id": str(row[0]),
            "channel": row[2],
            "recipient": row[3],
            "payload": row[4],
            "status": row[5],
            "created_at": str(row[6])
        }
    finally:
        db.close()
