from fastapi  import FastAPI 

app = FastAPI()

@app.get("/welcome")
def wel_come():
    return "FastAPI started Now ! "