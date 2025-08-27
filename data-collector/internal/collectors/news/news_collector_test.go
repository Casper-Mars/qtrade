package news

import (
	"context"
	"testing"
	"time"

	"data-collector/internal/models"
	"data-collector/internal/storage"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/bson/primitive"
)

// MockNewsRepository 模拟新闻存储库
type MockNewsRepository struct {
	newsList []*models.News
	existingNews map[string]bool // 用于模拟去重检查
}

func NewMockNewsRepository() *MockNewsRepository {
	return &MockNewsRepository{
		newsList:     make([]*models.News, 0),
		existingNews: make(map[string]bool),
	}
}

func (m *MockNewsRepository) Create(ctx context.Context, news *models.News) error {
	news.ID = primitive.NewObjectID()
	news.CreatedAt = time.Now()
	news.UpdatedAt = time.Now()
	m.newsList = append(m.newsList, news)
	return nil
}

func (m *MockNewsRepository) BatchCreate(ctx context.Context, newsList []*models.News) error {
	for _, news := range newsList {
		if err := m.Create(ctx, news); err != nil {
			return err
		}
	}
	return nil
}

func (m *MockNewsRepository) GetByID(ctx context.Context, id primitive.ObjectID) (*models.News, error) {
	for _, news := range m.newsList {
		if news.ID == id {
			return news, nil
		}
	}
	return nil, nil
}

func (m *MockNewsRepository) GetList(ctx context.Context, filter bson.M, limit, offset int64) ([]*models.News, error) {
	return m.newsList, nil
}

func (m *MockNewsRepository) GetByTimeRange(ctx context.Context, startTime, endTime time.Time, limit, offset int64) ([]*models.News, error) {
	var result []*models.News
	for _, news := range m.newsList {
		if news.PublishTime.After(startTime) && news.PublishTime.Before(endTime) {
			result = append(result, news)
		}
	}
	return result, nil
}

func (m *MockNewsRepository) SearchByKeyword(ctx context.Context, keyword string, limit, offset int64) ([]*models.News, error) {
	return m.newsList, nil
}

func (m *MockNewsRepository) GetByRelatedStock(ctx context.Context, stockCode string, limit, offset int64) ([]*models.News, error) {
	return m.newsList, nil
}

func (m *MockNewsRepository) Update(ctx context.Context, id primitive.ObjectID, update bson.M) error {
	return nil
}

func (m *MockNewsRepository) Delete(ctx context.Context, id primitive.ObjectID) error {
	return nil
}

func (m *MockNewsRepository) Exists(ctx context.Context, title, content string) (bool, error) {
	key := title + "|" + content
	return m.existingNews[key], nil
}

func (m *MockNewsRepository) Count(ctx context.Context, filter bson.M) (int64, error) {
	return int64(len(m.newsList)), nil
}

// 添加已存在的新闻（用于测试去重）
func (m *MockNewsRepository) AddExistingNews(title, content string) {
	key := title + "|" + content
	m.existingNews[key] = true
}

// TestNewCLSNewsCollector 测试创建财联社新闻采集器
func TestNewCLSNewsCollector(t *testing.T) {
	mockRepo := NewMockNewsRepository()
	collector := NewCLSNewsCollector(mockRepo)

	if collector == nil {
		t.Error("Expected non-nil collector")
	}

	// 验证采集器类型
	clsCollector, ok := collector.(*CLSNewsCollector)
	if !ok {
		t.Error("Expected CLSNewsCollector type")
	}

	if clsCollector.newsRepo == nil {
		t.Error("Expected non-nil newsRepo")
	}

	if clsCollector.collector == nil {
		t.Error("Expected non-nil colly collector")
	}
}

// TestParsePublishTime 测试发布时间解析
func TestParsePublishTime(t *testing.T) {
	mockRepo := NewMockNewsRepository()
	collector := NewCLSNewsCollector(mockRepo).(*CLSNewsCollector)

	tests := []struct {
		name     string
		timeStr  string
		expected bool // 是否期望解析成功
	}{
		{"今天时间格式", "14:30", true},
		{"昨天时间格式", "昨天 09:15", true},
		{"日期时间格式", "01-15 16:45", true},
		{"无效格式", "invalid time", true}, // 会返回当前时间
		{"空字符串", "", true},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result, err := collector.parsePublishTime(tt.timeStr)
			if tt.expected {
				if err != nil {
					t.Errorf("Expected no error, got %v", err)
				}
				if result.IsZero() {
					t.Error("Expected non-zero time")
				}
			} else {
				if err == nil {
					t.Error("Expected error, got nil")
				}
			}
		})
	}
}

// TestExtractRelatedStocks 测试关联股票提取
func TestExtractRelatedStocks(t *testing.T) {
	mockRepo := NewMockNewsRepository()
	collector := NewCLSNewsCollector(mockRepo).(*CLSNewsCollector)

	tests := []struct {
		name     string
		text     string
		expected int // 期望提取的股票数量
	}{
		{"包含上交所股票", "中国平安(601318)今日涨停", 1},
		{"包含深交所股票", "万科A(000002)发布公告", 1},
		{"包含创业板股票", "宁德时代(300750)业绩预告", 1},
		{"包含多只股票", "关注601318、000002、300750等个股", 3},
		{"不包含股票代码", "今日大盘上涨", 0},
		{"包含无效代码", "123456不是有效股票代码", 0},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			stocks := collector.extractRelatedStocks(tt.text)
			if len(stocks) != tt.expected {
				t.Errorf("Expected %d stocks, got %d", tt.expected, len(stocks))
			}
		})
	}
}

// TestExtractRelatedIndustries 测试关联行业提取
func TestExtractRelatedIndustries(t *testing.T) {
	mockRepo := NewMockNewsRepository()
	collector := NewCLSNewsCollector(mockRepo).(*CLSNewsCollector)

	tests := []struct {
		name     string
		text     string
		expected []string
	}{
		{"银行行业", "银行股集体上涨", []string{"银行"}},
		{"汽车行业", "新能源汽车销量大增", []string{"汽车", "电力设备"}},
		{"医药行业", "医药板块表现强势", []string{"医药生物"}},
		{"多个行业", "银行、保险、证券三大金融板块齐涨", []string{"银行", "保险", "证券"}},
		{"无相关行业", "今日天气不错", []string{}},
	}

	for _, tt := range tests {
			t.Run(tt.name, func(t *testing.T) {
				industries := collector.extractRelatedIndustries(tt.text)
				if len(industries) != len(tt.expected) {
					t.Errorf("Expected %d industries, got %d", len(tt.expected), len(industries))
					return
				}
				for _, expected := range tt.expected {
					found := false
					for _, industry := range industries {
						if industry == expected {
							found = true
							break
						}
					}
					if !found {
						t.Errorf("Expected industry %s not found", expected)
					}
				}
			})
		}
}

// TestIsValidNews 测试新闻数据验证
func TestIsValidNews(t *testing.T) {
	mockRepo := NewMockNewsRepository()
	collector := NewCLSNewsCollector(mockRepo).(*CLSNewsCollector)

	tests := []struct {
		name     string
		news     *models.News
		expected bool
	}{
		{
			"有效新闻",
			&models.News{
				Title:       "测试标题",
				Content:     "测试内容",
				Source:      "财联社",
				PublishTime: time.Now(),
			},
			true,
		},
		{
			"空标题",
			&models.News{
				Title:       "",
				Content:     "测试内容",
				Source:      "财联社",
				PublishTime: time.Now(),
			},
			false,
		},
		{
			"空内容",
			&models.News{
				Title:       "测试标题",
				Content:     "",
				Source:      "财联社",
				PublishTime: time.Now(),
			},
			false,
		},
		{
			"空来源",
			&models.News{
				Title:       "测试标题",
				Content:     "测试内容",
				Source:      "",
				PublishTime: time.Now(),
			},
			false,
		},
		{
			"零值时间",
			&models.News{
				Title:       "测试标题",
				Content:     "测试内容",
				Source:      "财联社",
				PublishTime: time.Time{},
			},
			false,
		},
		{"nil新闻", nil, false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := collector.isValidNews(tt.news)
			if result != tt.expected {
				t.Errorf("Expected %v, got %v", tt.expected, result)
			}
		})
	}
}

// TestGetCollectorInfo 测试获取采集器信息
func TestGetCollectorInfo(t *testing.T) {
	mockRepo := NewMockNewsRepository()
	collector := NewCLSNewsCollector(mockRepo)

	info := collector.GetCollectorInfo()

	if info == nil {
		t.Error("Expected non-nil collector info")
		return
	}

	// 验证必要字段
	expectedFields := []string{"name", "description", "source", "frequency", "data_type", "features"}
	for _, field := range expectedFields {
		if _, exists := info[field]; !exists {
			t.Errorf("Expected field %s not found in collector info", field)
		}
	}

	// 验证具体值
	if info["name"] != "财联社快讯采集器" {
		t.Errorf("Expected name '财联社快讯采集器', got %v", info["name"])
	}

	if info["source"] != "https://www.cls.cn/telegraph" {
		t.Errorf("Expected source 'https://www.cls.cn/telegraph', got %v", info["source"])
	}
}

// TestCLSNewsCollector_Interface 测试接口实现
func TestCLSNewsCollector_Interface(t *testing.T) {
	mockRepo := NewMockNewsRepository()
	var _ NewsCollector = NewCLSNewsCollector(mockRepo)
}

// TestMockNewsRepository_Interface 测试Mock存储库接口实现
func TestMockNewsRepository_Interface(t *testing.T) {
	var _ storage.NewsRepository = NewMockNewsRepository()
}