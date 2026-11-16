
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from middleware.logging_middleware import logging_middleware

from routers import (
    auth_router,
    user_router,
    category_router,
    product_router,
    cart_router,
    order_router,
    order_item_router,
    cancellation_router,
    review_router,
    payment_router
)

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s"
)

app = FastAPI(
    title="E-Commerce Order Management System",
    version="1.0.0"
)

app.middleware("http")(logging_middleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"]
)


@app.get("/")
def welcome():
    return {
        "message": "Welcome to my E-Commerce Order Management System!"
    }


app.include_router(auth_router.router)
app.include_router(user_router.router)
app.include_router(category_router.router)
app.include_router(product_router.router)
app.include_router(cart_router.router)
app.include_router(order_router.router)
app.include_router(order_item_router.router)
app.include_router(cancellation_router.router)
app.include_router(review_router.router)
app.include_router(payment_router.router)
