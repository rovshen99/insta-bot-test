from dotenv import load_dotenv
from fastapi import FastAPI
from routers.instagram import instagram_router

load_dotenv()

app = FastAPI()
app.include_router(instagram_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
