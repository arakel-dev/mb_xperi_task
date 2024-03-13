from fastapi import FastAPI
import uvicorn
from search import lookup
from fastapi.responses import JSONResponse
app = FastAPI()


@app.get("/")
def load_home():
    return {"homepage": True}


@app.get("/search", status_code=200)
def search_song(title: str):
    result = str()
    http_status_code = int
    try:
        result, http_status_code = lookup(title=title)
    except Exception as e:
        result = "Failed"
        http_status_code = 500
    finally:
        return JSONResponse(status_code=http_status_code,
                            content={title: result})


if __name__ == "__main__":
    config = uvicorn.Config(app="app:app",
                            host="0.0.0.0",
                            port=8080,
                            log_level="info")
    server = uvicorn.Server(config)
    server.run()
