
import uvicorn

from mensa_mcp import config
from mensa_mcp.server import mcp

app = mcp.sse_app()


def main():
    uvicorn.run(
        "mensa_mcp:app",
        host=config.HOST,
        port=config.PORT,
        workers=config.WORKERS,
        log_level=config.LOG_LEVEL,
        reload=False,
    )
