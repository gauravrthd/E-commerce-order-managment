
from itertools import count

db = {
    "users": {},
    "categories": {},
    "products": {},
    "cart": {},
    "orders": {},
    "order_items": {},
    "cancellations": {},
    "reviews": {},
    "payments": {}
}

counters = {
    table: count(1) for table in db
}


def next_id(table: str) -> int:
    return next(counters[table])


# Demo users for testing Module 3.
# They do not have login credentials.
demo_users = [
    ("Customer Demo", "customer@example.com", "9000000001", "customer"),
    ("Shopkeeper Demo", "shopkeeper@example.com", "9000000002", "shopkeeper"),
    ("Admin Demo", "admin@example.com", "9000000003", "admin"),
]

for name, email, mobile, role in demo_users:
    user_id = next_id("users")

    db["users"][user_id] = {
        "id": user_id,
        "name": name,
        "email": email,
        "mobile": mobile,
        "role": role,
        "hashed_password": None
    }
