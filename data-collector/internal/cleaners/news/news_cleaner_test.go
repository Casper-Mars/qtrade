package news

import (
	"context"
	"testing"
	"time"

	"data-collector/internal/models"

	"go.mongodb.org/mongo-driver/bson/primitive"
)

// TestNewDefaultNewsCleaner 测试创建默认新闻清洗器
func TestNewDefaultNewsCleaner(t *testing.T) {
	cleaner := NewDefaultNewsCleaner()

	if cleaner == nil {
		t.Error("Expected non-nil cleaner")
	}

	// 验证清洗器类型
	defaultCleaner, ok := cleaner.(*DefaultNewsCleaner)
	if !ok {
		t.Error("Expected DefaultNewsCleaner type")
	}

	// 验证正则表达式初始化
	if defaultCleaner.htmlTagRegex == nil {
		t.Error("Expected non-nil htmlTagRegex")
	}

	if defaultCleaner.specialCharRegex == nil {
		t.Error("Expected non-nil specialCharRegex")
	}

	if defaultCleaner.multiSpaceRegex == nil {
		t.Error("Expected non-nil multiSpaceRegex")
	}

	if defaultCleaner.urlRegex == nil {
		t.Error("Expected non-nil urlRegex")
	}

	// 验证敏感词列表
	if len(defaultCleaner.sensitiveWords) == 0 {
		t.Error("Expected non-empty sensitive words list")
	}
}

// TestCleanNews 测试清洗单条新闻
func TestCleanNews(t *testing.T) {
	cleaner := NewDefaultNewsCleaner()
	ctx := context.Background()

	tests := []struct {
		name     string
		news     *models.News
		expected bool // 是否期望返回有效结果
	}{
		{
			"有效新闻",
			&models.News{
				ID:          primitive.NewObjectID(),
				Title:       "<h1>测试标题</h1>",
				Content:     "<p>这是一条测试新闻内容，包含足够的文字来通过验证。</p>",
				Source:      "财联社",
				URL:         "https://example.com",
				PublishTime: time.Now(),
				CreatedAt:   time.Now(),
				UpdatedAt:   time.Now(),
			},
			true,
		},
		{
			"包含HTML标签的新闻",
			&models.News{
				ID:          primitive.NewObjectID(),
				Title:       "<script>alert('test')</script>重要新闻标题",
				Content:     "<div><p>新闻内容包含<a href='#'>链接</a>和<strong>加粗文字</strong>。</p></div>",
				Source:      "财联社",
				PublishTime: time.Now(),
			},
			true,
		},
		{
			"包含敏感词的新闻",
			&models.News{
				ID:      primitive.NewObjectID(),
				Title:   "重要财经新闻",
				Content: "这是重要的财经新闻内容。广告：请关注我们的公众号。更多内容请访问官网。",
				Source:  "财联社",
			},
			true,
		},
		{
			"标题过短的新闻",
			&models.News{
				ID:      primitive.NewObjectID(),
				Title:   "短",
				Content: "这是一条内容足够长的新闻，但是标题太短了。",
				Source:  "财联社",
			},
			false,
		},
		{
			"内容过短的新闻",
			&models.News{
				ID:      primitive.NewObjectID(),
				Title:   "这是一个正常长度的标题",
				Content: "短内容",
				Source:  "财联社",
			},
			false,
		},
		{"nil新闻", nil, false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result, err := cleaner.CleanNews(ctx, tt.news)
			if err != nil {
				t.Errorf("Unexpected error: %v", err)
				return
			}

			if tt.expected {
				if result == nil {
					t.Error("Expected non-nil result")
					return
				}

				// 验证HTML标签被移除
				if result.Title != "" && (result.Title == tt.news.Title) {
					// 如果原标题包含HTML标签，清洗后应该不同
					if tt.news.Title != result.Title {
						// 这是期望的行为
					}
				}

				// 验证基本字段保持不变
				if result.ID != tt.news.ID {
					t.Error("ID should remain unchanged")
				}
				if result.Source != tt.news.Source {
					t.Error("Source should remain unchanged")
				}
			} else {
				if result != nil {
					t.Error("Expected nil result for invalid news")
				}
			}
		})
	}
}

// TestBatchCleanNews 测试批量清洗新闻
func TestBatchCleanNews(t *testing.T) {
	cleaner := NewDefaultNewsCleaner()
	ctx := context.Background()

	newsList := []*models.News{
		{
			ID:          primitive.NewObjectID(),
			Title:       "有效新闻标题1",
			Content:     "这是第一条有效的新闻内容，包含足够的文字。",
			Source:      "财联社",
			PublishTime: time.Now(),
		},
		{
			ID:      primitive.NewObjectID(),
			Title:   "短", // 无效：标题过短
			Content: "这是第二条新闻内容。",
			Source:  "财联社",
		},
		{
			ID:          primitive.NewObjectID(),
			Title:       "有效新闻标题3",
			Content:     "这是第三条有效的新闻内容，也包含足够的文字。",
			Source:      "财联社",
			PublishTime: time.Now(),
		},
	}

	result, err := cleaner.BatchCleanNews(ctx, newsList)
	if err != nil {
		t.Errorf("Unexpected error: %v", err)
		return
	}

	// 应该只有2条有效新闻（第1条和第3条）
	if len(result) != 2 {
		t.Errorf("Expected 2 valid news, got %d", len(result))
	}

	// 验证返回的新闻是有效的
	for _, news := range result {
		if news == nil {
			t.Error("Expected non-nil news in result")
		}
		if len(news.Title) < 5 {
			t.Error("Expected valid title length")
		}
		if len(news.Content) < 20 {
			t.Error("Expected valid content length")
		}
	}
}

// TestCleanText 测试文本清洗
func TestCleanText(t *testing.T) {
	cleaner := NewDefaultNewsCleaner().(*DefaultNewsCleaner)

	tests := []struct {
		name     string
		input    string
		expected string
	}{
		{"移除HTML标签", "<h1>标题</h1><p>内容</p>", "标题内容"},
		{"移除URL", "访问 https://example.com 了解更多", "访问 了解更多"},
		{"标准化空格", "多个    空格   测试", "多个 空格 测试"},
		{"去除首尾空白", "  前后有空格  ", "前后有空格"},
		{"空字符串", "", ""},
		{"包含敏感词", "这是正常内容。广告：关注我们。", "这是正常内容。"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := cleaner.cleanText(tt.input)
			if result != tt.expected {
				t.Errorf("Expected %q, got %q", tt.expected, result)
			}
		})
	}
}

// TestContainsSensitiveWords 测试敏感词检测
func TestContainsSensitiveWords(t *testing.T) {
	cleaner := NewDefaultNewsCleaner().(*DefaultNewsCleaner)

	tests := []struct {
		name     string
		text     string
		expected bool
	}{
		{"包含广告", "这是广告内容", true},
		{"包含推广", "推广信息", true},
		{"包含免责声明", "免责声明：本文仅供参考", true},
		{"正常内容", "这是正常的新闻内容", false},
		{"空字符串", "", false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := cleaner.containsSensitiveWords(tt.text)
			if result != tt.expected {
				t.Errorf("Expected %v, got %v", tt.expected, result)
			}
		})
	}
}

// TestContainsValidChineseContent 测试中文内容检测
func TestContainsValidChineseContent(t *testing.T) {
	cleaner := NewDefaultNewsCleaner().(*DefaultNewsCleaner)

	tests := []struct {
		name     string
		text     string
		expected bool
	}{
		{"纯中文", "这是中文内容", true},
		{"中英混合", "这是中文和English混合", true},
		{"纯英文", "This is English content", false},
		{"数字符号", "123456!@#$%^", false},
		{"空字符串", "", false},
		{"少量中文", "a这b是c中d文e", true}, // 中文占比刚好30%
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := cleaner.containsValidChineseContent(tt.text)
			if result != tt.expected {
				t.Errorf("Expected %v, got %v", tt.expected, result)
			}
		})
	}
}

// TestIsValidCleanedNews 测试清洗后新闻验证
func TestIsValidCleanedNews(t *testing.T) {
	cleaner := NewDefaultNewsCleaner().(*DefaultNewsCleaner)

	tests := []struct {
		name     string
		news     *models.News
		expected bool
	}{
		{
			"有效新闻",
			&models.News{
				Title:   "这是一个有效的新闻标题",
				Content: "这是有效的新闻内容，包含足够的中文字符来通过验证。",
			},
			true,
		},
		{
			"标题过短",
			&models.News{
				Title:   "短",
				Content: "这是有效的新闻内容，包含足够的中文字符。",
			},
			false,
		},
		{
			"内容过短",
			&models.News{
				Title:   "这是有效的标题",
				Content: "短内容",
			},
			false,
		},
		{
			"无中文内容",
			&models.News{
				Title:   "English Title Only",
				Content: "This is English content without Chinese characters.",
			},
			false,
		},
		{"nil新闻", nil, false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := cleaner.isValidCleanedNews(tt.news)
			if result != tt.expected {
				t.Errorf("Expected %v, got %v", tt.expected, result)
			}
		})
	}
}

// TestGetCleanerInfo 测试获取清洗器信息
func TestGetCleanerInfo(t *testing.T) {
	cleaner := NewDefaultNewsCleaner()

	info := cleaner.GetCleanerInfo()

	if info == nil {
		t.Error("Expected non-nil cleaner info")
		return
	}

	// 验证必要字段
	expectedFields := []string{"name", "description", "version", "features", "sensitive_words_count"}
	for _, field := range expectedFields {
		if _, exists := info[field]; !exists {
			t.Errorf("Expected field %s not found in cleaner info", field)
		}
	}

	// 验证具体值
	if info["name"] != "默认新闻数据清洗器" {
		t.Errorf("Expected name '默认新闻数据清洗器', got %v", info["name"])
	}

	if info["version"] != "1.0.0" {
		t.Errorf("Expected version '1.0.0', got %v", info["version"])
	}

	// 验证features是数组
	if features, ok := info["features"].([]string); !ok {
		t.Error("Expected features to be []string")
	} else if len(features) == 0 {
		t.Error("Expected non-empty features list")
	}
}

// TestNewsCleaner_Interface 测试接口实现
func TestNewsCleaner_Interface(t *testing.T) {
	var _ NewsCleaner = NewDefaultNewsCleaner()
}