"""NLP模块测试配置文件"""

import pytest
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def mock_torch_device():
    """模拟torch设备，避免GPU依赖"""
    import torch
    return torch.device("cpu")


@pytest.fixture(autouse=True)
def reset_singletons():
    """自动重置单例实例，确保测试隔离"""
    from src.nlp.model_manager import NLPModelManager
    
    # 测试前重置
    NLPModelManager._instance = None
    
    yield
    
    # 测试后清理
    if NLPModelManager._instance:
        NLPModelManager._instance.clear_all_models()
    NLPModelManager._instance = None


@pytest.fixture
def sample_texts():
    """提供测试用的样本文本"""
    return {
        "positive": [
            "股票大幅上涨，投资者非常乐观",
            "公司盈利超预期，前景看好",
            "市场强势反弹，收益显著增长"
        ],
        "negative": [
            "股票暴跌，投资者恐慌抛售",
            "公司亏损严重，前景堪忧",
            "市场持续下滑，风险加剧"
        ],
        "neutral": [
            "今天天气不错",
            "会议将在下午举行",
            "系统正在维护中"
        ],
        "mixed": [
            "虽然股票上涨，但仍有下跌风险",
            "公司盈利增长，但面临激烈竞争",
            "市场机会与挑战并存"
        ]
    }


@pytest.fixture
def html_texts():
    """提供包含HTML标签的测试文本"""
    return [
        "<p>股票<strong>大幅上涨</strong></p>",
        "<div>公司<em>盈利</em>超预期</div>",
        "<span>市场<b>强势</b>反弹</span>"
    ]


@pytest.fixture
def url_texts():
    """提供包含URL的测试文本"""
    return [
        "访问 https://www.example.com 获取更多信息",
        "详情请见 http://finance.sina.com.cn",
        "参考链接：https://www.baidu.com/search?q=股票"
    ]


@pytest.fixture
def special_char_texts():
    """提供包含特殊字符的测试文本"""
    return [
        "股票@#$%上涨了！",
        "公司&*()盈利增长",
        "市场^%$#表现良好"
    ]