from fastapi  import FastAPI 
from pydantic import BaseModel

app = FastAPI()


class Product(BaseModel):
    name : str 
    categories : str
    price : int 


products = [
    Product(
        name = "laptop",
        categories= "electronic",
        price = 50000

    ),
    Product(
        name= "Shoes",
        categories= "Footwear",
        price = 500
    ),
    Product(
        name = "table",
        categories= "Furniture",
        price = 1500

    )
]

@app.get("/welcome")
def wel_come():
    return "FastAPI started Now ! "


@app.post("/product")
def create_product(product : Product):
    products.append(product)
    return product

@app.get("/products", response_model=list[Product])
def get_all_product():
    return products
