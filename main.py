
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

from observability.logging_config import configure_logging
from observability.request_middleware import ObservabilityMiddleware
from observability.metrics import metrics_endpoint


configure_logging()

app = FastAPI(
    title="E-Commerce Order Management System",
    description="FastAPI backend for managing users, products, carts, orders and payments",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


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


@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Welcome to my E-Commerce Order Management System!"
    }


app.add_api_route(
    "/metrics",
    metrics_endpoint,
    methods=["GET"],
    include_in_schema=False
)


app.add_middleware(ObservabilityMiddleware)
