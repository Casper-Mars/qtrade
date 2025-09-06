"""全局异常处理模块"""

import traceback
from typing import Any

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from loguru import logger


class QuantEngineException(Exception):
    """量化引擎基础异常类"""

    def __init__(
        self,
        message: str,
        error_code: str = "QUANT_ENGINE_ERROR",
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class DataCollectorException(QuantEngineException):
    """数据采集服务异常"""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message, error_code="DATA_COLLECTOR_ERROR", details=details
        )


class DatabaseException(QuantEngineException):
    """数据库操作异常"""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message=message, error_code="DATABASE_ERROR", details=details)


class RedisException(QuantEngineException):
    """Redis操作异常"""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message=message, error_code="REDIS_ERROR", details=details)


class FactorCalculationException(QuantEngineException):
    """因子计算异常"""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message, error_code="FACTOR_CALCULATION_ERROR", details=details
        )


class NLPException(QuantEngineException):
    """NLP处理异常"""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message=message, error_code="NLP_ERROR", details=details)


class ValidationException(QuantEngineException):
    """数据验证异常"""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message, error_code="VALIDATION_ERROR", details=details
        )


class ConfigurationException(QuantEngineException):
    """配置异常"""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message, error_code="CONFIGURATION_ERROR", details=details
        )


class DataNotFoundError(QuantEngineException):
    """数据未找到异常"""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message, error_code="DATA_NOT_FOUND_ERROR", details=details
        )


class DataSourceError(QuantEngineException):
    """数据源异常"""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message, error_code="DATA_SOURCE_ERROR", details=details
        )


async def quant_engine_exception_handler(
    request: Request, exc: QuantEngineException
) -> JSONResponse:
    """量化引擎异常处理器"""
    logger.error(
        f"QuantEngineException: {exc.error_code} - {exc.message}",
        extra={
            "error_code": exc.error_code,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method,
        },
    )

    return JSONResponse(
        status_code=400,
        content={
            "error": True,
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details,
            "path": request.url.path,
        },
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """HTTP异常处理器"""
    logger.warning(
        f"HTTPException: {exc.status_code} - {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "error_code": "HTTP_ERROR",
            "message": exc.detail,
            "status_code": exc.status_code,
            "path": request.url.path,
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """通用异常处理器"""
    error_id = id(exc)

    logger.error(
        f"未处理异常 [{error_id}]: {type(exc).__name__} - {str(exc)}",
        extra={
            "error_id": error_id,
            "exception_type": type(exc).__name__,
            "path": request.url.path,
            "method": request.method,
            "traceback": traceback.format_exc(),
        },
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "服务器内部错误",
            "error_id": error_id,
            "path": request.url.path,
        },
    )


def setup_exception_handlers(app: Any) -> None:
    """设置异常处理器"""
    app.add_exception_handler(QuantEngineException, quant_engine_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    logger.info("异常处理器设置完成")
