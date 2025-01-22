from fastapi import FastAPI
import starlette.responses as _responses

app = FastAPI()


@app.get("/")
async def root():
    return _responses.RedirectResponse("/redoc")
