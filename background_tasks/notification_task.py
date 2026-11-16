
from pathlib import Path
from datetime import datetime, timezone
from threading import Lock

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_FILE = LOG_DIR / "notifications.log"

lock = Lock()


def send_order_confirmation(email: str, order_id: int, total_amount: str):
    message = (
        f"{datetime.now(timezone.utc).isoformat()} | "
        f"Order ID: {order_id} | "
        f"Customer: {email} | "
        f"Amount: {total_amount} | "
        f"Order placed successfully\n"
    )

    with lock:
        LOG_DIR.mkdir(parents=True, exist_ok=True)

        with open(LOG_FILE, "a", encoding="utf-8") as file:
            file.write(message)
