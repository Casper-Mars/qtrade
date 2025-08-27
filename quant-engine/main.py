import uvicorn
from src.app import app
from src.config.settings import settings


def main():
    """主入口函数"""
    uvicorn.run(
        "src.app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    main()
