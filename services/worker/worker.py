import time, os, json
from sqlalchemy import create_engine, text
from jinja2 import Template

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/notifications_db")
engine = create_engine(DATABASE_URL, future=True)

POLL_INTERVAL = 3  # seconds

def resolve_template(template_body, payload):
    t = Template(template_body)
    return t.render(**(payload or {}))

def send_to_provider(channel, recipient, message):
    # MOCK provider: in production, integrate Twilio/SES/FCM
    print(f"[PROVIDER] channel={channel} recipient={recipient} message={message}")
    return {"status": "ok", "provider_id": "mock-123"}

def process_one(conn, row):
    nid = row['id']
    channel = row['channel']
    recipient = row['recipient']
    payload = row['payload'] or {}
    template_id = row['template_id']
    try:
        conn.execute(text("UPDATE notifications SET status='processing' WHERE id=:id"), {"id": nid})
        conn.commit()

        message = None
        if template_id:
            tpl = conn.execute(text("SELECT body FROM templates WHERE id=:id"), {"id": template_id}).fetchone()
            if tpl:
                message = resolve_template(tpl[0], payload)
            else:
                message = json.dumps(payload)
        else:
            message = json.dumps(payload)

        resp = send_to_provider(channel, recipient, message)

        conn.execute(text(
            "INSERT INTO notification_logs (notification_id, attempt_no, provider, provider_response, status) VALUES (:nid, :attempt, :provider, :resp, :status)"
        ), {"nid": nid, "attempt": 1, "provider": "mock", "resp": json.dumps(resp), "status": "success"})
        conn.execute(text("UPDATE notifications SET status='sent' WHERE id=:id"), {"id": nid})
        conn.commit()
        print(f"[WORKER] notification {nid} sent")
    except Exception as e:
        print("[WORKER] error:", e)
        conn.execute(text("UPDATE notifications SET status='failed' WHERE id=:id"), {"id": nid})
        conn.commit()

def worker_loop():
    print("Worker started, polling for queued notifications...")
    while True:
        with engine.connect() as conn:
            rows = conn.execute(text("SELECT id, channel, recipient, payload, template_id FROM notifications WHERE status='queued' ORDER BY created_at LIMIT 5")).mappings().all()
            if not rows:
                time.sleep(POLL_INTERVAL)
                continue
            for row in rows:
                process_one(conn, row)

if __name__ == "__main__":
    worker_loop()
