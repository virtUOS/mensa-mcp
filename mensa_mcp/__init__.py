
import uvicorn

from mensa_mcp import config


def main():
    uvicorn.run(
        "mensa_mcp.server:app",
        host=config.HOST,
        port=config.PORT,
        workers=config.WORKERS,
        log_level=config.LOG_LEVEL,
        reload=False,
    )
