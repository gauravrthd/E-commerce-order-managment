from fastapi import FastAPI

from routers import (
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

app = FastAPI(
    title="E-Commerce Order Management System",
    description="FastAPI Module 3 - Routing and Error Handling",
    version="1.0.0"
)


@app.get("/", tags=["Home"])
def welcome():
    return {
        "message": "Welcome to my E-Commerce Order Management System!"
    }


app.include_router(user_router.router)
app.include_router(category_router.router)
app.include_router(product_router.router)
app.include_router(cart_router.router)
app.include_router(order_router.router)
app.include_router(order_item_router.router)
app.include_router(cancellation_router.router)
app.include_router(review_router.router)
app.include_router(payment_router.router)
