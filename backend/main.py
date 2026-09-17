from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def status() :
    return {"message": "Completed"}