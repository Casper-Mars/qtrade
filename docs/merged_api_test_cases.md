# HTTP API 测试用例文档

## 概述

本文档提供量化交易系统所有HTTP API接口的测试用例，包括因子计算引擎、因子组合管理、回测任务管理和回测引擎相关的API接口测试。

## 测试环境

- **服务地址**: `http://localhost:8000`
- **API版本**: `v1`
- **基础路径**: `/api/v1`
- **认证方式**: 无（内部服务）

---

# 第一部分：因子计算引擎 API 测试用例

## 1. 统一因子计算 API 测试用例

### 1.1 计算所有因子

**接口路径**: `POST /api/v1/factor-engine/unified/calculate-all`

#### 测试用例 1.1.1: 正常计算单个股票所有因子

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/factor-engine/unified/calculate-all" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "000001.SZ",
    "calculation_date": "2024-01-15"
  }' \
  -w "\n"
```

**期望响应**:
```json
{
  "code": 200,
  "message": "所有因子计算完成",
  "data": {
    "stock_code": "000001.SZ",
    "calculation_date": "2024-01-15",
    "technical_factors": {
      "ma_5": 12.45,
      "ma_20": 12.30,
      "rsi_14": 65.2,
      "macd": 0.15
    },
    "fundamental_factors": {
      "roe": 0.125,
      "roa": 0.08,
      "debt_ratio": 0.45
    },
    "market_factors": {
      "beta": 1.2,
      "volatility": 0.25,
      "turnover_rate": 0.03
    },
    "sentiment_factors": {
      "news_sentiment": 0.65,
      "social_sentiment": 0.58
    }
  }
}
```

#### 测试用例 1.1.2: 无效股票代码

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/factor-engine/unified/calculate-all" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "INVALID",
    "calculation_date": "2024-01-15"
  }' \
  -w "\n"
```

**期望响应**:
```json
{
  "detail": "无效的股票代码格式: INVALID"
}
```

#### 测试用例 1.1.3: 无效日期格式

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/factor-engine/unified/calculate-all" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "000001.SZ",
    "calculation_date": "2024/01/15"
  }' \
  -w "\n"
```

**期望响应**:
```json
{
  "detail": "日期格式不正确，应为YYYY-MM-DD"
}
```

### 1.2 批量计算所有因子

**接口路径**: `POST /api/v1/factor-engine/unified/batch-calculate-all`

#### 测试用例 1.2.1: 正常批量计算

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/factor-engine/unified/batch-calculate-all" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_codes": ["000001.SZ", "000002.SZ", "600000.SH"],
    "calculation_date": "2024-01-15"
  }' \
  -w "\n"
```

**期望响应**:
```json
{
  "code": 200,
  "message": "批量因子计算完成",
  "data": {
    "calculation_date": "2024-01-15",
    "total_stocks": 3,
    "successful_stocks": 3,
    "failed_stocks": 0,
    "results": [
      {
        "stock_code": "000001.SZ",
        "technical_factors": {
          "ma_5": 12.45,
          "ma_20": 12.30
        },
        "fundamental_factors": {
          "roe": 0.125
        },
        "market_factors": {
          "beta": 1.2
        },
        "sentiment_factors": {
          "news_sentiment": 0.65
        }
      }
    ],
    "errors": null
  }
}
```

#### 测试用例 1.2.2: 部分股票计算失败

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/factor-engine/unified/batch-calculate-all" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_codes": ["000001.SZ", "INVALID", "600000.SH"],
    "calculation_date": "2024-01-15"
  }' \
  -w "\n"
```

**期望响应**:
```json
{
  "code": 200,
  "message": "批量因子计算完成",
  "data": {
    "calculation_date": "2024-01-15",
    "total_stocks": 3,
    "successful_stocks": 2,
    "failed_stocks": 1,
    "results": [
      {
        "stock_code": "000001.SZ",
        "technical_factors": {
          "ma_5": 12.45
        }
      },
      {
        "stock_code": "600000.SH",
        "technical_factors": {
          "ma_5": 15.20
        }
      }
    ],
    "errors": [
      {
        "stock_code": "INVALID",
        "error": "无效的股票代码格式"
      }
    ]
  }
}
```

### 1.3 获取所有因子历史数据

**接口路径**: `GET /api/v1/factor-engine/unified/history`

#### 测试用例 1.3.1: 正常获取历史数据

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/factor-engine/unified/history?stock_code=000001.SZ&start_date=2024-01-01&end_date=2024-01-15&limit=10" \
  -w "\n"
```

**期望响应**:
```json
{
  "code": 200,
  "message": "获取历史数据成功",
  "data": {
    "stock_code": "000001.SZ",
    "start_date": "2024-01-01",
    "end_date": "2024-01-15",
    "count": 10,
    "factors": [
      {
        "calculation_date": "2024-01-15",
        "technical_factors": {
          "ma_5": 12.45,
          "ma_20": 12.30
        },
        "fundamental_factors": {
          "roe": 0.125
        },
        "market_factors": {
          "beta": 1.2
        },
        "sentiment_factors": {
          "news_sentiment": 0.65
        }
      }
    ]
  }
}
```

## 2. 技术因子 API 测试用例

### 2.1 计算技术因子

**接口路径**: `POST /api/v1/factor-engine/technical/calculate`

#### 测试用例 2.1.1: 正常计算技术因子

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/factor-engine/technical/calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "000001.SZ",
    "calculation_date": "2024-01-15",
    "factors": ["ma_5", "ma_20", "rsi_14", "macd"]
  }' \
  -w "\n"
```

**期望响应**:
```json
{
  "code": 200,
  "message": "技术因子计算完成",
  "data": {
    "stock_code": "000001.SZ",
    "calculation_date": "2024-01-15",
    "factors": {
      "ma_5": 12.45,
      "ma_20": 12.30,
      "rsi_14": 65.2,
      "macd": 0.15
    }
  }
}
```

#### 测试用例 2.1.2: 不支持的技术因子

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/factor-engine/technical/calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "000001.SZ",
    "calculation_date": "2024-01-15",
    "factors": ["unsupported_factor"]
  }' \
  -w "\n"
```

**期望响应**:
```json
{
  "detail": "不支持的技术因子: unsupported_factor"
}
```

### 2.2 获取技术因子历史数据

**接口路径**: `GET /api/v1/factor-engine/technical/history`

#### 测试用例 2.2.1: 正常获取技术因子历史

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/factor-engine/technical/history?stock_code=000001.SZ&start_date=2024-01-01&end_date=2024-01-15&factors=ma_5,rsi_14&limit=10" \
  -w "\n"
```

**期望响应**:
```json
{
  "code": 200,
  "message": "获取技术因子历史数据成功",
  "data": {
    "stock_code": "000001.SZ",
    "start_date": "2024-01-01",
    "end_date": "2024-01-15",
    "factors": ["ma_5", "rsi_14"],
    "count": 10,
    "data": [
      {
        "calculation_date": "2024-01-15",
        "ma_5": 12.45,
        "rsi_14": 65.2
      }
    ]
  }
}
```

### 2.3 批量计算技术因子

**接口路径**: `POST /api/v1/factor-engine/technical/batch-calculate`

#### 测试用例 2.3.1: 正常批量计算技术因子

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/factor-engine/technical/batch-calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_codes": ["000001.SZ", "000002.SZ"],
    "calculation_date": "2024-01-15",
    "factors": ["ma_5", "rsi_14"]
  }' \
  -w "\n"
```

**期望响应**:
```json
{
  "code": 200,
  "message": "批量技术因子计算完成",
  "data": {
    "calculation_date": "2024-01-15",
    "factors": ["ma_5", "rsi_14"],
    "total_stocks": 2,
    "successful_stocks": 2,
    "failed_stocks": 0,
    "results": [
      {
        "stock_code": "000001.SZ",
        "factors": {
          "ma_5": 12.45,
          "rsi_14": 65.2
        }
      },
      {
        "stock_code": "000002.SZ",
        "factors": {
          "ma_5": 8.90,
          "rsi_14": 45.8
        }
      }
    ],
    "errors": null
  }
}
```

## 3. 基本面因子 API 测试用例

### 3.1 计算基本面因子

**接口路径**: `POST /api/v1/factor-engine/fundamental/calculate`

#### 测试用例 3.1.1: 正常计算基本面因子

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/factor-engine/fundamental/calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "000001.SZ",
    "calculation_date": "2024-01-15",
    "factors": ["roe", "roa", "debt_ratio", "pe_ratio"]
  }' \
  -w "\n"
```

**期望响应**:
```json
{
  "code": 200,
  "message": "基本面因子计算完成",
  "data": {
    "stock_code": "000001.SZ",
    "calculation_date": "2024-01-15",
    "factors": {
      "roe": 0.125,
      "roa": 0.08,
      "debt_ratio": 0.45,
      "pe_ratio": 12.5
    }
  }
}
```

#### 测试用例 3.1.2: 财务数据不足

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/factor-engine/fundamental/calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "NEW001.SZ",
    "calculation_date": "2024-01-15",
    "factors": ["roe", "roa"]
  }' \
  -w "\n"
```

**期望响应**:
```json
{
  "detail": "股票 NEW001.SZ 缺少必要的财务数据"
}
```

### 3.2 获取基本面因子历史数据

**接口路径**: `GET /api/v1/factor-engine/fundamental/history`

#### 测试用例 3.2.1: 正常获取基本面因子历史

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/factor-engine/fundamental/history?stock_code=000001.SZ&start_date=2024-01-01&end_date=2024-01-15&factors=roe,roa&limit=10" \
  -w "\n"
```

**期望响应**:
```json
{
  "code": 200,
  "message": "获取基本面因子历史数据成功",
  "data": {
    "stock_code": "000001.SZ",
    "start_date": "2024-01-01",
    "end_date": "2024-01-15",
    "factors": ["roe", "roa"],
    "count": 5,
    "data": [
      {
        "calculation_date": "2024-01-15",
        "roe": 0.125,
        "roa": 0.08
      }
    ]
  }
}
```

### 3.3 批量计算基本面因子

**接口路径**: `POST /api/v1/factor-engine/fundamental/batch-calculate`

#### 测试用例 3.3.1: 正常批量计算基本面因子

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/factor-engine/fundamental/batch-calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_codes": ["000001.SZ", "600000.SH"],
    "calculation_date": "2024-01-15",
    "factors": ["roe", "debt_ratio"]
  }' \
  -w "\n"
```

**期望响应**:
```json
{
  "code": 200,
  "message": "批量基本面因子计算完成",
  "data": {
    "calculation_date": "2024-01-15",
    "factors": ["roe", "debt_ratio"],
    "total_stocks": 2,
    "successful_stocks": 2,
    "failed_stocks": 0,
    "results": [
      {
        "stock_code": "000001.SZ",
        "factors": {
          "roe": 0.125,
          "debt_ratio": 0.45
        }
      },
      {
        "stock_code": "600000.SH",
        "factors": {
          "roe": 0.15,
          "debt_ratio": 0.38
        }
      }
    ],
    "errors": null
  }
}
```

## 4. 市场因子 API 测试用例

### 4.1 计算市场因子

**接口路径**: `POST /api/v1/factor-engine/market/calculate`

#### 测试用例 4.1.1: 正常计算市场因子

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/factor-engine/market/calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "000001.SZ",
    "calculation_date": "2024-01-15",
    "factors": ["beta", "volatility", "turnover_rate", "market_cap"]
  }' \
  -w "\n"
```

**期望响应**:
```json
{
  "code": 200,
  "message": "市场因子计算完成",
  "data": {
    "stock_code": "000001.SZ",
    "calculation_date": "2024-01-15",
    "factors": {
      "beta": 1.2,
      "volatility": 0.25,
      "turnover_rate": 0.03,
      "market_cap": 150000000000
    }
  }
}
```

#### 测试用例 4.1.2: 市场数据不足

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/factor-engine/market/calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "000001.SZ",
    "calculation_date": "2020-01-01",
    "factors": ["beta", "volatility"]
  }' \
  -w "\n"
```

**期望响应**:
```json
{
  "detail": "股票 000001.SZ 在 2020-01-01 缺少足够的市场数据"
}
```

### 4.2 获取市场因子历史数据

**接口路径**: `GET /api/v1/factor-engine/market/history`

#### 测试用例 4.2.1: 正常获取市场因子历史

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/factor-engine/market/history?stock_code=000001.SZ&start_date=2024-01-01&end_date=2024-01-15&factors=beta,volatility&limit=10" \
  -w "\n"
```

**期望响应**:
```json
{
  "code": 200,
  "message": "获取市场因子历史数据成功",
  "data": {
    "stock_code": "000001.SZ",
    "start_date": "2024-01-01",
    "end_date": "2024-01-15",
    "factors": ["beta", "volatility"],
    "count": 10,
    "data": [
      {
        "calculation_date": "2024-01-15",
        "beta": 1.2,
        "volatility": 0.25
      }
    ]
  }
}
```

### 4.3 批量计算市场因子

**接口路径**: `POST /api/v1/factor-engine/market/batch-calculate`

#### 测试用例 4.3.1: 正常批量计算市场因子

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/factor-engine/market/batch-calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_codes": ["000001.SZ", "000002.SZ"],
    "calculation_date": "2024-01-15",
    "factors": ["beta", "turnover_rate"]
  }' \
  -w "\n"
```

**期望响应**:
```json
{
  "code": 200,
  "message": "批量市场因子计算完成",
  "data": {
    "calculation_date": "2024-01-15",
    "factors": ["beta", "turnover_rate"],
    "total_stocks": 2,
    "successful_stocks": 2,
    "failed_stocks": 0,
    "results": [
      {
        "stock_code": "000001.SZ",
        "factors": {
          "beta": 1.2,
          "turnover_rate": 0.03
        }
      },
      {
        "stock_code": "000002.SZ",
        "factors": {
          "beta": 0.9,
          "turnover_rate": 0.025
        }
      }
    ],
    "errors": null
  }
}
```

## 5. 情感因子 API 测试用例

### 5.1 计算情感因子

**接口路径**: `POST /api/v1/factor-engine/sentiment/calculate`

#### 测试用例 5.1.1: 正常计算情感因子

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/factor-engine/sentiment/calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "000001.SZ",
    "calculation_date": "2024-01-15"
  }' \
  -w "\n"
```

**期望响应**:
```json
{
  "code": 200,
  "message": "情绪因子计算完成",
  "data": {
    "stock_code": "000001.SZ",
    "calculation_date": "2024-01-15",
    "sentiment_score": 0.65,
    "news_count": 25,
    "positive_ratio": 0.68,
    "negative_ratio": 0.12,
    "neutral_ratio": 0.20,
    "confidence_score": 0.85
  }
}
```

#### 测试用例 5.1.2: 无新闻数据

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/factor-engine/sentiment/calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "999999.SZ",
    "calculation_date": "2024-01-15"
  }' \
  -w "\n"
```

**期望响应**:
```json
{
  "detail": "股票 999999.SZ 在 2024-01-15 没有找到相关新闻数据"
}
```

### 5.2 批量计算情感因子

**接口路径**: `POST /api/v1/factor-engine/sentiment/batch-calculate`

#### 测试用例 5.2.1: 正常批量计算情感因子

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/factor-engine/sentiment/batch-calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_codes": ["000001.SZ", "000002.SZ"],
    "calculation_date": "2024-01-15"
  }' \
  -w "\n"
```

**期望响应**:
```json
{
  "code": 200,
  "message": "批量情绪因子计算完成",
  "data": {
    "calculation_date": "2024-01-15",
    "total_stocks": 2,
    "successful_stocks": 2,
    "failed_stocks": 0,
    "results": [
      {
        "stock_code": "000001.SZ",
        "sentiment_score": 0.65,
        "news_count": 25,
        "confidence_score": 0.85
      },
      {
        "stock_code": "000002.SZ",
        "sentiment_score": 0.58,
        "news_count": 18,
        "confidence_score": 0.78
      }
    ],
    "errors": null
  }
}
```

### 5.3 获取情感因子

**接口路径**: `GET /api/v1/factor-engine/sentiment/factor/{stock_code}`

#### 测试用例 5.3.1: 正常获取情感因子

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/factor-engine/sentiment/factor/000001.SZ?calculation_date=2024-01-15" \
  -w "\n"
```

**期望响应**:
```json
{
  "code": 200,
  "message": "获取情绪因子成功",
  "data": {
    "stock_code": "000001.SZ",
    "calculation_date": "2024-01-15",
    "sentiment_score": 0.65,
    "news_count": 25,
    "positive_ratio": 0.68,
    "negative_ratio": 0.12,
    "neutral_ratio": 0.20,
    "confidence_score": 0.85
  }
}
```

#### 测试用例 5.3.2: 数据不存在

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/factor-engine/sentiment/factor/000001.SZ?calculation_date=2020-01-01" \
  -w "\n"
```

**期望响应**:
```json
{
  "detail": "未找到股票 000001.SZ 在 2020-01-01 的情绪因子数据"
}
```

### 5.4 获取指定日期的所有情感因子

**接口路径**: `GET /api/v1/factor-engine/sentiment/factors/date/{calculation_date}`

#### 测试用例 5.4.1: 正常获取指定日期的所有情感因子

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/factor-engine/sentiment/factors/date/2024-01-15?limit=50" \
  -w "\n"
```

**期望响应**:
```json
{
  "code": 200,
  "message": "获取 2024-01-15 情绪因子数据成功",
  "data": {
    "calculation_date": "2024-01-15",
    "count": 50,
    "factors": [
      {
        "stock_code": "000001.SZ",
        "sentiment_score": 0.65,
        "news_count": 25,
        "confidence_score": 0.85
      },
      {
        "stock_code": "000002.SZ",
        "sentiment_score": 0.58,
        "news_count": 18,
        "confidence_score": 0.78
      }
    ]
  }
}
```

### 5.5 获取情感趋势

**接口路径**: `POST /api/v1/factor-engine/sentiment/trend`

#### 测试用例 5.5.1: 正常获取情感趋势

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/factor-engine/sentiment/trend" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "000001.SZ",
    "days": 30
  }' \
  -w "\n"
```

**期望响应**:
```json
{
  "code": 200,
  "message": "获取情绪趋势成功",
  "data": {
    "stock_code": "000001.SZ",
    "period": "30天",
    "daily_factors": [
      {
        "calculation_date": "2024-01-15",
        "sentiment_score": 0.65,
        "news_count": 25
      },
      {
        "calculation_date": "2024-01-14",
        "sentiment_score": 0.62,
        "news_count": 22
      }
    ],
    "statistics": {
      "avg_sentiment": 0.635,
      "max_sentiment": 0.78,
      "min_sentiment": 0.45,
      "sentiment_volatility": 0.12,
      "total_news": 650
    }
  }
}
```

### 5.6 情感因子服务健康检查

**接口路径**: `GET /api/v1/factor-engine/sentiment/health`

#### 测试用例 5.6.1: 正常健康检查

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/factor-engine/sentiment/health" \
  -w "\n"
```

**期望响应**:
```json
{
  "code": 200,
  "message": "健康检查完成",
  "data": {
    "service": "sentiment-factor",
    "status": "healthy",
    "model_status": {
      "nlp_model_loaded": true,
      "sentiment_analyzer_ready": true
    },
    "database_status": "healthy",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

#### 测试用例 5.6.2: 服务异常情况

**期望响应**:
```json
{
  "code": 500,
  "message": "健康检查失败",
  "data": {
    "service": "sentiment-factor",
    "status": "unhealthy",
    "error": "数据库连接失败",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

---

# 第二部分：第三迭代（回测框架建设）API 测试用例

## 6. 因子组合配置管理 API 测试用例

### 6.1 创建因子组合配置

**接口路径**: `POST /api/v1/factor-config/create`

#### 测试用例 6.1.1: 正常创建因子组合配置

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/factor-config/create" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "000001.SZ",
    "description": "平安银行多因子组合策略",
    "technical_factors": ["ma_5", "ma_20", "rsi_14", "macd"],
    "fundamental_factors": ["roe", "roa", "debt_ratio"],
    "sentiment_factors": ["news_sentiment"],
    "factor_weights": {
      "ma_5": 0.15,
      "ma_20": 0.15,
      "rsi_14": 0.10,
      "macd": 0.10,
      "roe": 0.20,
      "roa": 0.15,
      "debt_ratio": 0.10,
      "news_sentiment": 0.05
    }
  }' \
  -w "\n"
```

**期望响应**:
```json
{
  "code": 200,
  "message": "配置创建成功",
  "data": {
    "config_id": "fc_20240107_001",
    "stock_code": "000001.SZ",
    "description": "平安银行多因子组合策略",
    "technical_factors": ["ma_5", "ma_20", "rsi_14", "macd"],
    "fundamental_factors": ["roe", "roa", "debt_ratio"],
    "sentiment_factors": ["news_sentiment"],
    "factor_weights": {
      "ma_5": 0.15,
      "ma_20": 0.15,
      "rsi_14": 0.10,
      "macd": 0.10,
      "roe": 0.20,
      "roa": 0.15,
      "debt_ratio": 0.10,
      "news_sentiment": 0.05
    },
    "created_at": "2024-01-07T10:00:00Z",
    "updated_at": "2024-01-07T10:00:00Z"
  }
}
```

#### 测试用例 6.1.2: 权重总和不等于1的错误情况

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/factor-config/create" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "000002.SZ",
    "description": "权重错误测试",
    "technical_factors": ["ma_5", "rsi_14"],
    "fundamental_factors": ["roe"],
    "sentiment_factors": [],
    "factor_weights": {
      "ma_5": 0.3,
      "rsi_14": 0.3,
      "roe": 0.3
    }
  }' \
  -w "\n"
```

**期望响应**:
```json
{
  "detail": "因子权重总和必须等于1.0，当前总和为0.9"
}
```

### 6.2 获取因子组合配置

**接口路径**: `POST /api/v1/factor-config/get`

#### 测试用例 6.2.1: 正常获取配置

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/factor-config/get" \
  -H "Content-Type: application/json" \
  -d '{
    "config_id": "fc_20240107_001"
  }' \
  -w "\n"
```

**期望响应**:
```json
{
  "code": 200,
  "message": "获取配置成功",
  "data": {
    "config_id": "fc_20240107_001",
    "stock_code": "000001.SZ",
    "description": "平安银行多因子组合策略",
    "technical_factors": ["ma_5", "ma_20", "rsi_14", "macd"],
    "fundamental_factors": ["roe", "roa", "debt_ratio"],
    "sentiment_factors": ["news_sentiment"],
    "factor_weights": {
      "ma_5": 0.15,
      "ma_20": 0.15,
      "rsi_14": 0.10,
      "macd": 0.10,
      "roe": 0.20,
      "roa": 0.15,
      "debt_ratio": 0.10,
      "news_sentiment": 0.05
    },
    "created_at": "2024-01-07T10:00:00Z",
    "updated_at": "2024-01-07T10:00:00Z"
  }
}
```

#### 测试用例 6.2.2: 配置不存在的情况

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/factor-config/get" \
  -H "Content-Type: application/json" \
  -d '{
    "config_id": "non_existent_config"
  }' \
  -w "\n"
```

**期望响应**:
```json
{
  "detail": "因子组合配置不存在: non_existent_config"
}
```

### 6.3 按股票代码获取配置

**接口路径**: `POST /api/v1/factor-config/get-by-stock`

#### 测试用例 6.3.1: 正常按股票代码获取

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/factor-config/get-by-stock" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "000001.SZ"
  }' \
  -w "\n"
```

**期望响应**:
```json
{
  "code": 200,
  "message": "获取配置成功",
  "data": [
    {
      "config_id": "fc_20240107_001",
      "stock_code": "000001.SZ",
      "description": "平安银行多因子组合策略",
      "technical_factors": ["ma_5", "ma_20", "rsi_14", "macd"],
      "fundamental_factors": ["roe", "roa", "debt_ratio"],
      "sentiment_factors": ["news_sentiment"],
      "factor_weights": {
        "ma_5": 0.15,
        "ma_20": 0.15,
        "rsi_14": 0.10,
        "macd": 0.10,
        "roe": 0.20,
        "roa": 0.15,
        "debt_ratio": 0.10,
        "news_sentiment": 0.05
      },
      "created_at": "2024-01-07T10:00:00Z",
      "updated_at": "2024-01-07T10:00:00Z"
    }
  ]
}
```

### 6.4 更新因子组合配置

**接口路径**: `POST /api/v1/factor-config/update`

#### 测试用例 6.4.1: 正常更新配置

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/factor-config/update" \
  -H "Content-Type: application/json" \
  -d '{
    "config_id": "fc_20240107_001",
    "description": "平安银行优化多因子组合策略",
    "technical_factors": ["ma_5", "ma_20", "rsi_14"],
    "fundamental_factors": ["roe", "roa"],
    "sentiment_factors": ["news_sentiment"],
    "factor_weights": {
      "ma_5": 0.20,
      "ma_20": 0.20,
      "rsi_14": 0.15,
      "roe": 0.25,
      "roa": 0.15,
      "news_sentiment": 0.05
    }
  }' \
  -w "\n"
```

**期望响应**:
```json
{
  "code": 200,
  "message": "配置更新成功",
  "data": {
    "config_id": "fc_20240107_001",
    "stock_code": "000001.SZ",
    "description": "平安银行优化多因子组合策略",
    "technical_factors": ["ma_5", "ma_20", "rsi_14"],
    "fundamental_factors": ["roe", "roa"],
    "sentiment_factors": ["news_sentiment"],
    "factor_weights": {
      "ma_5": 0.20,
      "ma_20": 0.20,
      "rsi_14": 0.15,
      "roe": 0.25,
      "roa": 0.15,
      "news_sentiment": 0.05
    },
    "created_at": "2024-01-07T10:00:00Z",
    "updated_at": "2024-01-07T11:30:00Z"
  }
}
```

### 6.5 删除因子组合配置

**接口路径**: `POST /api/v1/factor-config/delete`

#### 测试用例 6.5.1: 正常删除配置

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/factor-config/delete" \
  -H "Content-Type: application/json" \
  -d '{
    "config_id": "fc_20240107_001"
  }' \
  -w "\n"
```

**期望响应**:
```json
{
  "code": 200,
  "message": "配置删除成功",
  "data": {
    "config_id": "fc_20240107_001",
    "deleted": true
  }
}
```

### 6.6 获取配置列表

**接口路径**: `POST /api/v1/factor-config/list`

#### 测试用例 6.6.1: 正常获取配置列表

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/factor-config/list" \
  -H "Content-Type: application/json" \
  -d '{
    "page": 1,
    "page_size": 10
  }' \
  -w "\n"
```

**期望响应**:
```json
{
  "code": 200,
  "message": "获取配置列表成功",
  "data": {
    "items": [
      {
        "config_id": "fc_20240107_002",
        "stock_code": "000002.SZ",
        "description": "万科A多因子组合策略",
        "created_at": "2024-01-07T11:00:00Z",
        "updated_at": "2024-01-07T11:00:00Z"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 10,
    "total_pages": 1
  }
}
```

## 7. 回测任务管理 API 测试用例

### 7.1 创建回测任务

**接口路径**: `POST /api/v1/backtest/createTask`

#### 测试用例 7.1.1: 正常创建单个回测任务

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/backtest/createTask" \
  -H "Content-Type: application/json" \
  -d '{
    "task_name": "平安银行因子回测",
    "stock_code": "000001.SZ",
    "start_date": "2020-01-01",
    "end_date": "2023-12-31",
    "initial_capital": 1000000.0,
    "factor_combination_id": "fc_20240107_001",
    "config": {
      "transaction_cost": 0.001,
      "slippage": 0.0001
    }
  }' \
  -w "\n"
```

**期望响应**:
```json
{
  "task_id": "bt_20240107_001",
  "batch_id": "batch_20240107_001",
  "status": "pending",
  "message": "任务创建成功"
}
```

#### 测试用例 7.1.2: 批量创建回测任务

**请求示例**:
```bash
# 创建第一个任务
curl -X POST "http://localhost:8000/api/v1/backtest/createTask" \
  -H "Content-Type: application/json" \
  -d '{
    "task_name": "万科A因子回测",
    "stock_code": "000002.SZ",
    "start_date": "2020-01-01",
    "end_date": "2023-12-31",
    "initial_capital": 1000000.0,
    "factor_combination_id": "fc_20240107_002",
    "batch_id": "batch_20240107_002"
  }' \
  -w "\n"

# 创建第二个任务（同一批次）
curl -X POST "http://localhost:8000/api/v1/backtest/createTask" \
  -H "Content-Type: application/json" \
  -d '{
    "task_name": "招商银行因子回测",
    "stock_code": "600036.SH",
    "start_date": "2020-01-01",
    "end_date": "2023-12-31",
    "initial_capital": 1000000.0,
    "factor_combination_id": "fc_20240107_003",
    "batch_id": "batch_20240107_002"
  }' \
  -w "\n"
```

#### 测试用例 7.1.3: 参数验证失败情况

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/backtest/createTask" \
  -H "Content-Type: application/json" \
  -d '{
    "task_name": "参数错误测试",
    "stock_code": "invalid_code",
    "start_date": "2023-12-31",
    "end_date": "2020-01-01",
    "initial_capital": -1000
  }' \
  -w "\n"
```

**期望响应**:
```json
{
  "detail": "参数验证失败: 开始日期不能晚于结束日期，初始资金必须大于0"
}
```

### 7.2 查询任务状态

**接口路径**: `GET /api/v1/backtest/getTaskStatus`

#### 测试用例 7.2.1: 正常查询任务状态

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/backtest/getTaskStatus?task_id=bt_20240107_001" \
  -w "\n"
```

**期望响应**:
```json
{
  "task_id": "bt_20240107_001",
  "task_name": "平安银行因子回测",
  "status": "completed",
  "batch_id": "batch_20240107_001",
  "stock_code": "000001.SZ",
  "created_at": "2024-01-07T10:00:00Z",
  "started_at": "2024-01-07T10:01:00Z",
  "completed_at": "2024-01-07T10:15:00Z",
  "error_message": null,
  "backtest_result_id": "br_20240107_001"
}
```

#### 测试用例 7.2.2: 查询不存在的任务

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/backtest/getTaskStatus?task_id=non_existent_task" \
  -w "\n"
```

**期望响应**:
```json
{
  "detail": "任务不存在: non_existent_task"
}
```

### 7.3 按批次查询任务

**接口路径**: `GET /api/v1/backtest/getTasksByBatch`

#### 测试用例 7.3.1: 正常按批次查询

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/backtest/getTasksByBatch?batch_id=batch_20240107_002" \
  -w "\n"
```

**期望响应**:
```json
{
  "batch_id": "batch_20240107_002",
  "tasks": [
    {
      "task_id": "bt_20240107_002",
      "task_name": "万科A因子回测",
      "status": "completed",
      "batch_id": "batch_20240107_002",
      "stock_code": "000002.SZ",
      "created_at": "2024-01-07T11:00:00Z",
      "started_at": "2024-01-07T11:01:00Z",
      "completed_at": "2024-01-07T11:20:00Z",
      "error_message": null,
      "backtest_result_id": "br_20240107_002"
    },
    {
      "task_id": "bt_20240107_003",
      "task_name": "招商银行因子回测",
      "status": "running",
      "batch_id": "batch_20240107_002",
      "stock_code": "600036.SH",
      "created_at": "2024-01-07T11:05:00Z",
      "started_at": "2024-01-07T11:06:00Z",
      "completed_at": null,
      "error_message": null,
      "backtest_result_id": null
    }
  ],
  "total_count": 2
}
```

### 7.4 获取任务结果

**接口路径**: `GET /api/v1/backtest/getTaskResult`

#### 测试用例 7.4.1: 正常获取任务结果

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/backtest/getTaskResult?task_id=bt_20240107_001" \
  -w "\n"
```

**期望响应**:
```json
{
  "task_id": "bt_20240107_001",
  "task_name": "平安银行因子回测",
  "status": "completed",
  "backtest_result_id": "br_20240107_001",
  "created_at": "2024-01-07T10:00:00Z",
  "started_at": "2024-01-07T10:01:00Z",
  "completed_at": "2024-01-07T10:15:00Z",
  "duration": 840.5,
  "error_message": null
}
```

#### 测试用例 7.4.2: 任务未完成情况

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/backtest/getTaskResult?task_id=bt_20240107_003" \
  -w "\n"
```

**期望响应**:
```json
{
  "detail": "任务尚未完成，无法获取结果"
}
```

### 7.5 取消任务

**接口路径**: `POST /api/v1/backtest/cancelTask`

#### 测试用例 7.5.1: 正常取消任务

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/backtest/cancelTask" \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "bt_20240107_003"
  }' \
  -w "\n"
```

**期望响应**:
```json
{
  "task_id": "bt_20240107_003",
  "status": "cancelled",
  "message": "任务已取消"
}
```

#### 测试用例 7.5.2: 取消已完成的任务

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/backtest/cancelTask" \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "bt_20240107_001"
  }' \
  -w "\n"
```

**期望响应**:
```json
{
  "detail": "无法取消已完成的任务"
}
```

## 8. 系统健康检查 API 测试用例

### 8.1 因子计算引擎健康检查

**接口路径**: `GET /api/v1/factor-engine/health`

#### 测试用例 8.1.1: 正常健康检查

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/factor-engine/health" \
  -w "\n"
```

**期望响应**:
```json
{
  "service": "factor-engine",
  "status": "healthy",
  "timestamp": "2024-01-07T10:00:00Z",
  "components": {
    "database": "healthy",
    "redis": "healthy",
    "technical_calculator": "healthy",
    "fundamental_calculator": "healthy",
    "market_calculator": "healthy",
    "sentiment_calculator": "healthy"
  }
}
```

### 8.2 回测引擎健康检查

**接口路径**: `GET /api/v1/backtest/health`

#### 测试用例 8.2.1: 正常健康检查

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/backtest/health" \
  -w "\n"
```

**期望响应**:
```json
{
  "service": "backtest-engine",
  "status": "healthy",
  "timestamp": "2024-01-07T10:00:00Z",
  "components": {
    "database": "healthy",
    "task_queue": "healthy",
    "factor_engine_connection": "healthy"
  }
}
```

## 9. 集成测试用例

### 9.1 完整因子计算到回测流程

#### 测试用例 9.1.1: 端到端流程测试

**步骤1: 创建因子组合配置**
```bash
curl -X POST "http://localhost:8000/api/v1/factor-config/create" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "000001.SZ",
    "description": "集成测试因子组合",
    "technical_factors": ["ma_5", "rsi_14"],
    "fundamental_factors": ["roe"],
    "sentiment_factors": ["news_sentiment"],
    "factor_weights": {
      "ma_5": 0.3,
      "rsi_14": 0.2,
      "roe": 0.4,
      "news_sentiment": 0.1
    }
  }' \
  -w "\n"
```

**步骤2: 计算因子**
```bash
curl -X POST "http://localhost:8000/api/v1/factor-engine/unified/calculate-all" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "000001.SZ",
    "calculation_date": "2024-01-15"
  }' \
  -w "\n"
```

**步骤3: 创建回测任务**
```bash
curl -X POST "http://localhost:8000/api/v1/backtest/createTask" \
  -H "Content-Type: application/json" \
  -d '{
    "task_name": "集成测试回测",
    "stock_code": "000001.SZ",
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "initial_capital": 1000000.0,
    "factor_combination_id": "fc_20240107_004"
  }' \
  -w "\n"
```

**步骤4: 查询回测结果**
```bash
curl -X GET "http://localhost:8000/api/v1/backtest/getTaskResult?task_id=bt_20240107_004" \
  -w "\n"
```

## 10. 性能测试用例

### 10.1 批量因子计算性能测试

#### 测试用例 10.1.1: 大批量股票因子计算

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/factor-engine/unified/batch-calculate-all" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_codes": ["000001.SZ", "000002.SZ", "600000.SH", "600036.SH", "000858.SZ"],
    "calculation_date": "2024-01-15"
  }' \
  -w "\n"
```

**性能要求**:
- 响应时间 < 30秒
- 成功率 > 95%

### 10.2 并发回测任务性能测试

#### 测试用例 10.2.1: 并发创建多个回测任务

**测试脚本**:
```bash
#!/bin/bash
for i in {1..10}; do
  curl -X POST "http://localhost:8000/api/v1/backtest/createTask" \
    -H "Content-Type: application/json" \
    -d "{
      \"task_name\": \"并发测试任务$i\",
      \"stock_code\": \"00000$i.SZ\",
      \"start_date\": \"2023-01-01\",
      \"end_date\": \"2023-12-31\",
      \"initial_capital\": 1000000.0,
      \"factor_combination_id\": \"fc_20240107_001\"
    }" \
    -w "\n" &
done
wait
```

**性能要求**:
- 任务创建响应时间 < 5秒
- 系统稳定性良好

## 11. 错误处理测试用例

### 11.1 网络异常处理

#### 测试用例 11.1.1: 数据库连接异常

**模拟场景**: 数据库服务不可用

**期望响应**:
```json
{
  "detail": "数据库连接失败，请稍后重试"
}
```

#### 测试用例 11.1.2: 外部服务超时

**模拟场景**: 因子计算服务响应超时

**期望响应**:
```json
{
  "detail": "服务响应超时，请稍后重试"
}
```

### 11.2 数据异常处理

#### 测试用例 11.2.1: 股票数据缺失

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/factor-engine/technical/calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "999999.SZ",
    "calculation_date": "2024-01-15",
    "factors": ["ma_5", "rsi_14"]
  }' \
  -w "\n"
```

**期望响应**:
```json
{
  "detail": "股票 999999.SZ 的历史数据不足，无法计算技术因子"
}
```

#### 测试用例 11.2.2: 日期范围无效

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/factor-engine/unified/history?stock_code=000001.SZ&start_date=2024-12-31&end_date=2024-01-01" \
  -w "\n"
```

**期望响应**:
```json
{
  "detail": "开始日期不能晚于结束日期"
}
```

## 12. 测试数据清理

### 12.1 清理测试数据

#### 测试用例 12.1.1: 清理因子组合配置

**请求示例**:
```bash
# 删除测试创建的配置
curl -X POST "http://localhost:8000/api/v1/factor-config/delete" \
  -H "Content-Type: application/json" \
  -d '{
    "config_id": "fc_20240107_004"
  }' \
  -w "\n"
```

#### 测试用例 12.1.2: 清理回测任务

**请求示例**:
```bash
# 取消未完成的测试任务
curl -X POST "http://localhost:8000/api/v1/backtest/cancelTask" \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "bt_20240107_004"
  }' \
  -w "\n"
```

---

# 测试执行指南

## 测试环境准备

1. **启动服务**:
   ```bash
   # 启动因子计算引擎
   cd /path/to/quant-engine
   go run cmd/server/main.go
   
   # 启动回测引擎（如果是独立服务）
   cd /path/to/backtest-engine
   go run cmd/server/main.go
   ```

2. **数据库准备**:
   - 确保MySQL、Redis、MongoDB服务正常运行
   - 准备测试用的股票数据
   - 准备测试用的新闻数据

3. **测试数据**:
   - 股票代码: 000001.SZ, 000002.SZ, 600000.SH, 600036.SH
   - 测试日期范围: 2020-01-01 到 2024-01-15

## 测试执行顺序

1. **基础功能测试**: 按照文档顺序执行各个API的基本功能测试
2. **集成测试**: 执行端到端的完整流程测试
3. **性能测试**: 执行批量和并发测试
4. **异常测试**: 执行各种异常情况的测试
5. **清理测试**: 清理测试过程中产生的数据

## 测试结果验证

- **功能正确性**: 验证返回数据的格式和内容是否符合预期
- **性能指标**: 验证响应时间是否满足要求
- **错误处理**: 验证异常情况下的错误信息是否准确
- **数据一致性**: 验证相关联的数据是否保持一致

## 注意事项

1. **测试隔离**: 确保测试之间相互独立，不会相互影响
2. **数据清理**: 每次测试后及时清理测试数据
3. **环境一致**: 保持测试环境与生产环境的一致性
4. **监控日志**: 测试过程中注意观察系统日志，及时发现问题

---

## 修改记录

[2024-01-15 10:30] [新增] [创建因子计算引擎和第三迭代API测试用例合并文档]
[2024-01-15 10:30] [新增] [添加因子计算引擎所有API接口的测试用例]
[2024-01-15 10:30] [新增] [添加第三迭代回测框架相关API的测试用例]
[2024-01-15 10:30] [新增] [添加集成测试、性能测试、错误处理测试用例]
[2024-01-15 10:30] [新增] [添加测试执行指南和注意事项]