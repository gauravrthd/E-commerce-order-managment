
from fastapi import Header, HTTPException, Depends
from utils.store import db


def get_current_user(
    x_user_id: int = Header(alias="X-User-Id")
):
    user = db["users"].get(x_user_id)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid demo user ID"
        )

    return user


def allow_roles(*roles):

    def check_role(user=Depends(get_current_user)):
        if user["role"] not in roles:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission"
            )
        return user

    return check_role


def check_owner_or_admin(user, owner_id):
    if user["role"] != "admin" and user["id"] != owner_id:
        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )


def get_order_items(order_id):
    return [
        item for item in db["order_items"].values()
        if item["order_id"] == order_id
    ]


def can_manage_order(user, order_id):
    if user["role"] == "admin":
        return True

    if user["role"] != "shopkeeper":
        return False

    items = get_order_items(order_id)

    return bool(items) and all(
        db["products"].get(item["product_id"], {}).get("seller_id")
        == user["id"]
        for item in items
    )
