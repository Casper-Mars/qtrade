# Python项目Makefile

# 默认目标
.DEFAULT_GOAL := help

# 变量定义
PYTHON := python
UV := uv
SRC_DIR := src
TEST_DIR := tests

# 帮助信息
.PHONY: help
help:
	@echo "可用的make命令:"
	@echo "  install     - 安装项目依赖"
	@echo "  dev-install - 安装开发依赖"
	@echo "  lint        - 运行所有代码检查工具"
	@echo "  ruff-check  - 运行ruff代码检查"
	@echo "  ruff-fix    - 运行ruff自动修复"
	@echo "  mypy        - 运行mypy类型检查"
	@echo "  format      - 格式化代码"
	@echo "  test        - 运行测试"
	@echo "  clean       - 清理缓存文件"

# 安装依赖
.PHONY: install
install:
	$(UV) sync

# 安装开发依赖
.PHONY: dev-install
dev-install:
	$(UV) add --dev mypy ruff pytest
	$(UV) sync

# 运行所有代码检查
.PHONY: lint
lint: ruff-check mypy

# Ruff代码检查
.PHONY: ruff-check
ruff-check:
	$(UV) run ruff check $(SRC_DIR) $(TEST_DIR)

# Ruff自动修复
.PHONY: ruff-fix
ruff-fix:
	$(UV) run ruff check --fix $(SRC_DIR) $(TEST_DIR)

# Ruff格式化
.PHONY: ruff-format
ruff-format:
	$(UV) run ruff format $(SRC_DIR) $(TEST_DIR)

# MyPy类型检查
.PHONY: mypy
mypy:
	$(UV) run mypy $(SRC_DIR)

# 格式化代码（包含ruff格式化）
.PHONY: format
format: ruff-format

# 运行测试
.PHONY: test
test:
	$(UV) run pytest $(TEST_DIR)

# 清理缓存文件
.PHONY: clean
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +