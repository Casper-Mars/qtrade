"""全局日志配置模块"""

import sys
from pathlib import Path

from loguru import logger

from ..config.settings import settings


def setup_logger(log_file: str | None = None, log_level: str = "INFO") -> None:
    """配置全局日志"""
    # 移除默认的日志处理器
    logger.remove()

    # 日志格式
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    # 控制台日志
    logger.add(
        sys.stdout,
        format=log_format,
        level=log_level,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # 文件日志
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # 普通日志文件
        logger.add(
            log_file,
            format=log_format,
            level=log_level,
            rotation="100 MB",
            retention="30 days",
            compression="zip",
            backtrace=True,
            diagnose=True,
            encoding="utf-8",
        )

        # 错误日志文件
        error_log_file = log_path.parent / f"{log_path.stem}_error{log_path.suffix}"
        logger.add(
            str(error_log_file),
            format=log_format,
            level="ERROR",
            rotation="50 MB",
            retention="60 days",
            compression="zip",
            backtrace=True,
            diagnose=True,
            encoding="utf-8",
        )

    logger.info(f"日志系统初始化完成，级别: {log_level}")
    if log_file:
        logger.info(f"日志文件: {log_file}")


def init_logger() -> None:
    """初始化日志系统"""
    setup_logger(log_file=settings.log_file, log_level=settings.log_level)


# 导出logger实例
__all__ = ["logger", "setup_logger", "init_logger"]
