# 第三迭代 HTTP API 测试用例文档

## 概述

本文档提供第三迭代（回测框架建设）所有HTTP API接口的测试用例，包括因子组合管理、回测任务管理和回测引擎相关的API接口测试。

## 测试环境

- **服务地址**: `http://localhost:8000`
- **API版本**: `v1`
- **基础路径**: `/api/v1`
- **认证方式**: 无（内部服务）

## 1. 因子组合配置管理 API 测试用例

### 1.1 创建因子组合配置

**接口路径**: `POST /api/v1/factor-config/create`

#### 测试用例 1.1.1: 正常创建因子组合配置

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

#### 测试用例 1.1.2: 权重总和不等于1的错误情况

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

### 1.2 获取因子组合配置

**接口路径**: `POST /api/v1/factor-config/get`

#### 测试用例 1.2.1: 正常获取配置

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

#### 测试用例 1.2.2: 配置不存在的情况

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

### 1.3 按股票代码获取配置

**接口路径**: `POST /api/v1/factor-config/get-by-stock`

#### 测试用例 1.3.1: 正常按股票代码获取

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

### 1.4 更新因子组合配置

**接口路径**: `POST /api/v1/factor-config/update`

#### 测试用例 1.4.1: 正常更新配置

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

### 1.5 删除因子组合配置

**接口路径**: `POST /api/v1/factor-config/delete`

#### 测试用例 1.5.1: 正常删除配置

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

### 1.6 获取配置列表

**接口路径**: `POST /api/v1/factor-config/list`

#### 测试用例 1.6.1: 正常获取配置列表

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

## 2. 回测任务管理 API 测试用例

### 2.1 创建回测任务

**接口路径**: `POST /api/v1/backtest/createTask`

#### 测试用例 2.1.1: 正常创建单个回测任务

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

#### 测试用例 2.1.2: 批量创建回测任务

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

#### 测试用例 2.1.3: 参数验证失败情况

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

### 2.2 查询任务状态

**接口路径**: `GET /api/v1/backtest/getTaskStatus`

#### 测试用例 2.2.1: 正常查询任务状态

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

#### 测试用例 2.2.2: 查询不存在的任务

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

### 2.3 按批次查询任务

**接口路径**: `GET /api/v1/backtest/getTasksByBatch`

#### 测试用例 2.3.1: 正常按批次查询

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

### 2.4 获取任务结果

**接口路径**: `GET /api/v1/backtest/getTaskResult`

#### 测试用例 2.4.1: 正常获取任务结果

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

#### 测试用例 2.4.2: 获取未完成任务的结果

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/backtest/getTaskResult?task_id=bt_20240107_003" \
  -w "\n"
```

**期望响应**:
```json
{
  "task_id": "bt_20240107_003",
  "task_name": "招商银行因子回测",
  "status": "running",
  "backtest_result_id": null,
  "created_at": "2024-01-07T11:05:00Z",
  "started_at": "2024-01-07T11:06:00Z",
  "completed_at": null,
  "duration": null,
  "error_message": null
}
```

### 2.5 取消任务

**接口路径**: `POST /api/v1/backtest/cancelTask`

#### 测试用例 2.5.1: 正常取消任务

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
  "success": true,
  "message": "任务取消成功"
}
```

#### 测试用例 2.5.2: 取消已完成的任务

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
  "task_id": "bt_20240107_001",
  "success": false,
  "message": "任务已完成，无法取消"
}
```

## 3. 系统健康检查 API 测试用例

### 3.1 健康检查

**接口路径**: `GET /health`

#### 测试用例 3.1.1: 正常健康检查

**请求示例**:
```bash
curl -X GET "http://localhost:8000/health" \
  -w "\n"
```

**期望响应**:
```json
{
  "status": "ok",
  "service": "quant-engine",
  "version": "0.1.0",
  "health": {
    "overall": true,
    "mysql": {
      "status": "ok",
      "response_time": 5.2
    },
    "redis": {
      "status": "ok",
      "response_time": 1.8
    }
  }
}
```

### 3.2 API版本信息

**接口路径**: `GET /api/v1/health/version`

#### 测试用例 3.2.1: 获取版本信息

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/health/version" \
  -w "\n"
```

**期望响应**:
```json
{
  "service": "quant-engine",
  "version": "0.1.0",
  "api_version": "v1",
  "build_time": "2024-01-07T08:00:00Z",
  "git_commit": "abc123def456"
}
```

## 4. 集成测试场景

### 4.1 完整回测流程测试

#### 测试场景 4.1.1: 端到端回测流程

**步骤1**: 创建因子组合配置
```bash
curl -X POST "http://localhost:8000/api/v1/factor-config/create" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "000001.SZ",
    "description": "集成测试因子组合",
    "technical_factors": ["ma_5", "rsi_14"],
    "fundamental_factors": ["roe"],
    "sentiment_factors": [],
    "factor_weights": {
      "ma_5": 0.4,
      "rsi_14": 0.3,
      "roe": 0.3
    }
  }' \
  -w "\n"
```

**步骤2**: 创建回测任务
```bash
curl -X POST "http://localhost:8000/api/v1/backtest/createTask" \
  -H "Content-Type: application/json" \
  -d '{
    "task_name": "集成测试回测任务",
    "stock_code": "000001.SZ",
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "initial_capital": 1000000.0,
    "factor_combination_id": "fc_20240107_004"
  }' \
  -w "\n"
```

**步骤3**: 监控任务执行
```bash
# 循环查询任务状态直到完成
while true; do
  status=$(curl -s "http://localhost:8000/api/v1/backtest/getTaskStatus?task_id=bt_20240107_004" | jq -r '.status')
  echo "任务状态: $status"
  if [ "$status" = "completed" ] || [ "$status" = "failed" ]; then
    break
  fi
  sleep 10
done
```

**步骤4**: 获取任务结果
```bash
curl -X GET "http://localhost:8000/api/v1/backtest/getTaskResult?task_id=bt_20240107_004" \
  -w "\n"
```

### 4.2 批量任务测试

#### 测试场景 4.2.1: 多股票批量回测

**步骤1**: 创建多个因子配置
```bash
# 为不同股票创建因子配置
for stock in "000001.SZ" "000002.SZ" "600036.SH"; do
  curl -X POST "http://localhost:8000/api/v1/factor-config/create" \
    -H "Content-Type: application/json" \
    -d "{
      \"stock_code\": \"$stock\",
      \"description\": \"批量测试因子组合 - $stock\",
      \"technical_factors\": [\"ma_5\", \"rsi_14\"],
      \"fundamental_factors\": [\"roe\"],
      \"sentiment_factors\": [],
      \"factor_weights\": {
        \"ma_5\": 0.4,
        \"rsi_14\": 0.3,
        \"roe\": 0.3
      }
    }" \
    -w "\n"
done
```

**步骤2**: 创建批量回测任务
```bash
batch_id="batch_$(date +%Y%m%d_%H%M%S)"
for stock in "000001.SZ" "000002.SZ" "600036.SH"; do
  curl -X POST "http://localhost:8000/api/v1/backtest/createTask" \
    -H "Content-Type: application/json" \
    -d "{
      \"task_name\": \"批量回测任务 - $stock\",
      \"stock_code\": \"$stock\",
      \"start_date\": \"2023-01-01\",
      \"end_date\": \"2023-12-31\",
      \"initial_capital\": 1000000.0,
      \"batch_id\": \"$batch_id\"
    }" \
    -w "\n"
done
```

**步骤3**: 监控批次执行
```bash
# 查询批次状态
curl -X GET "http://localhost:8000/api/v1/backtest/getTasksByBatch?batch_id=$batch_id" \
  -w "\n"
```

## 5. 性能测试用例

### 5.1 并发创建任务测试

#### 测试用例 5.1.1: 并发创建100个任务

**测试脚本**:
```bash
#!/bin/bash
# 并发创建任务测试脚本

echo "开始并发创建任务测试..."
start_time=$(date +%s)

# 并发创建100个任务
for i in {1..100}; do
  {
    curl -X POST "http://localhost:8000/api/v1/backtest/createTask" \
      -H "Content-Type: application/json" \
      -d "{
        \"task_name\": \"并发测试任务_$i\",
        \"stock_code\": \"000001.SZ\",
        \"start_date\": \"2023-01-01\",
        \"end_date\": \"2023-03-31\",
        \"initial_capital\": 1000000.0
      }" \
      -w "\n" \
      -s > /dev/null
  } &
done

# 等待所有任务完成
wait

end_time=$(date +%s)
duration=$((end_time - start_time))
echo "并发创建100个任务耗时: ${duration}秒"
```

### 5.2 大数据量查询测试

#### 测试用例 5.2.1: 查询大量历史任务

**请求示例**:
```bash
# 查询大量配置列表
curl -X POST "http://localhost:8000/api/v1/factor-config/list" \
  -H "Content-Type: application/json" \
  -d '{
    "page": 1,
    "page_size": 1000
  }' \
  -w "响应时间: %{time_total}秒\n"
```

## 6. 错误处理测试用例

### 6.1 网络异常测试

#### 测试用例 6.1.1: 数据库连接异常

**模拟场景**: 停止MySQL服务后调用API

**请求示例**:
```bash
# 停止MySQL服务后执行
curl -X POST "http://localhost:8000/api/v1/factor-config/create" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "000001.SZ",
    "description": "数据库异常测试",
    "technical_factors": ["ma_5"],
    "fundamental_factors": [],
    "sentiment_factors": [],
    "factor_weights": {"ma_5": 1.0}
  }' \
  -w "\n"
```

**期望响应**:
```json
{
  "detail": "数据库连接失败，请稍后重试"
}
```

### 6.2 数据验证异常测试

#### 测试用例 6.2.1: 无效的股票代码

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/backtest/createTask" \
  -H "Content-Type: application/json" \
  -d '{
    "task_name": "无效股票代码测试",
    "stock_code": "INVALID.CODE",
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "initial_capital": 1000000.0
  }' \
  -w "\n"
```

**期望响应**:
```json
{
  "detail": "无效的股票代码格式: INVALID.CODE"
}
```

## 7. 测试数据清理

### 7.1 清理测试数据脚本

```bash
#!/bin/bash
# 清理测试数据脚本

echo "开始清理测试数据..."

# 删除测试创建的因子配置
for config_id in "fc_20240107_001" "fc_20240107_002" "fc_20240107_003" "fc_20240107_004"; do
  curl -X POST "http://localhost:8000/api/v1/factor-config/delete" \
    -H "Content-Type: application/json" \
    -d "{\"config_id\": \"$config_id\"}" \
    -s > /dev/null
  echo "删除配置: $config_id"
done

echo "测试数据清理完成"
```

## 8. 测试执行指南

### 8.1 测试前准备

1. **启动服务**:
   ```bash
   cd /Users/reachlucifer/project/qtrade/quant-engine
   python main.py
   ```

2. **检查服务状态**:
   ```bash
   curl http://localhost:8000/health
   ```

3. **准备测试工具**:
   - 安装 `curl` 命令行工具
   - 安装 `jq` JSON处理工具（可选）

### 8.2 测试执行顺序

1. **基础功能测试**: 按照章节1-3的顺序执行基础API测试
2. **集成测试**: 执行章节4的端到端流程测试
3. **性能测试**: 执行章节5的性能测试用例
4. **异常测试**: 执行章节6的错误处理测试
5. **数据清理**: 执行章节7的数据清理脚本

### 8.3 测试结果验证

- **响应状态码**: 正常情况应返回200，异常情况返回4xx或5xx
- **响应格式**: 所有响应应为有效的JSON格式
- **数据一致性**: 创建、查询、更新、删除操作的数据应保持一致
- **性能指标**: API响应时间应在合理范围内（通常<1秒）

### 8.4 常见问题排查

1. **连接被拒绝**: 检查服务是否正常启动
2. **数据库错误**: 检查MySQL和Redis服务状态
3. **权限错误**: 检查文件和目录权限
4. **端口冲突**: 检查8000端口是否被占用

---

**文档版本**: v1.0  
**最后更新**: 2024-01-07  
**维护者**: quant-engine开发团队