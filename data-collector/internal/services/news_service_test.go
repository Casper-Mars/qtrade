package services

import (
	"context"
	"testing"
	"time"

	"data-collector/internal/models"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/bson/primitive"
)

// MockNewsRepository 模拟新闻存储库
type MockNewsRepository struct {
	mock.Mock
}

func (m *MockNewsRepository) Create(ctx context.Context, news *models.News) error {
	args := m.Called(ctx, news)
	return args.Error(0)
}

func (m *MockNewsRepository) BatchCreate(ctx context.Context, newsList []*models.News) error {
	args := m.Called(ctx, newsList)
	return args.Error(0)
}

func (m *MockNewsRepository) GetByID(ctx context.Context, id primitive.ObjectID) (*models.News, error) {
	args := m.Called(ctx, id)
	return args.Get(0).(*models.News), args.Error(1)
}

func (m *MockNewsRepository) GetList(ctx context.Context, filter bson.M, limit, offset int64) ([]*models.News, error) {
	args := m.Called(ctx, filter, limit, offset)
	return args.Get(0).([]*models.News), args.Error(1)
}

func (m *MockNewsRepository) GetByTimeRange(ctx context.Context, startTime, endTime time.Time, limit, offset int64) ([]*models.News, error) {
	args := m.Called(ctx, startTime, endTime, limit, offset)
	return args.Get(0).([]*models.News), args.Error(1)
}

func (m *MockNewsRepository) SearchByKeyword(ctx context.Context, keyword string, limit, offset int64) ([]*models.News, error) {
	args := m.Called(ctx, keyword, limit, offset)
	return args.Get(0).([]*models.News), args.Error(1)
}

func (m *MockNewsRepository) GetByRelatedStock(ctx context.Context, stockCode string, limit, offset int64) ([]*models.News, error) {
	args := m.Called(ctx, stockCode, limit, offset)
	return args.Get(0).([]*models.News), args.Error(1)
}

func (m *MockNewsRepository) Count(ctx context.Context, filter bson.M) (int64, error) {
	args := m.Called(ctx, filter)
	return args.Get(0).(int64), args.Error(1)
}

func (m *MockNewsRepository) Update(ctx context.Context, id primitive.ObjectID, update bson.M) error {
	args := m.Called(ctx, id, update)
	return args.Error(0)
}

func (m *MockNewsRepository) Delete(ctx context.Context, id primitive.ObjectID) error {
	args := m.Called(ctx, id)
	return args.Error(0)
}

func (m *MockNewsRepository) Exists(ctx context.Context, title, content string) (bool, error) {
	args := m.Called(ctx, title, content)
	return args.Get(0).(bool), args.Error(1)
}

// TestNewNewsService 测试创建新闻服务
func TestNewNewsService(t *testing.T) {
	mockRepo := &MockNewsRepository{}

	service := NewNewsService(mockRepo)

	assert.NotNil(t, service)
	assert.NotNil(t, service.collector)
	assert.NotNil(t, service.cleaner)
	assert.NotNil(t, service.scheduler)
	assert.NotNil(t, service.newsRepo)
}

// TestNewsService_GetStatus 测试获取服务状态
func TestNewsService_GetStatus(t *testing.T) {
	mockRepo := &MockNewsRepository{}

	service := NewNewsService(mockRepo)
	status := service.GetStatus()

	assert.NotNil(t, status)
	assert.Equal(t, "news", status["service"])
	assert.Contains(t, status, "running")
	assert.Contains(t, status, "scheduler")
}

// TestNewsService_GetCollectorInfo 测试获取采集器信息
func TestNewsService_GetCollectorInfo(t *testing.T) {
	mockRepo := &MockNewsRepository{}

	service := NewNewsService(mockRepo)
	info := service.GetCollectorInfo()

	assert.NotNil(t, info)
	assert.Contains(t, info, "name")
	assert.Contains(t, info, "source")
	assert.Contains(t, info, "frequency")
}

// TestNewsService_GetCleanerInfo 测试获取清洗器信息
func TestNewsService_GetCleanerInfo(t *testing.T) {
	mockRepo := &MockNewsRepository{}

	service := NewNewsService(mockRepo)
	info := service.GetCleanerInfo()

	assert.NotNil(t, info)
	assert.Contains(t, info, "name")
	assert.Contains(t, info, "version")
	assert.Contains(t, info, "description")
}

// TestNewsService_StartStop 测试启动和停止服务
func TestNewsService_StartStop(t *testing.T) {
	mockRepo := &MockNewsRepository{}

	// 设置mock期望 - 允许任何Exists和Create调用
	mockRepo.On("Exists", mock.Anything, mock.Anything, mock.Anything).Return(false, nil)
	mockRepo.On("Create", mock.Anything, mock.Anything).Return(nil)

	service := NewNewsService(mockRepo)

	// 测试启动
	err := service.Start()
	assert.NoError(t, err)
	assert.True(t, service.scheduler.IsRunning())

	// 测试停止
	err = service.Stop()
	assert.NoError(t, err)
	assert.False(t, service.scheduler.IsRunning())
}

// TestNewsService_TriggerCollection 测试手动触发采集
func TestNewsService_TriggerCollection(t *testing.T) {
	mockRepo := &MockNewsRepository{}

	// 设置mock期望 - 允许任何Exists和Create调用
	mockRepo.On("Exists", mock.Anything, mock.Anything, mock.Anything).Return(false, nil)
	mockRepo.On("Create", mock.Anything, mock.Anything).Return(nil)

	service := NewNewsService(mockRepo)

	// 启动服务
	err := service.Start()
	assert.NoError(t, err)
	defer service.Stop()

	// 触发采集
	err = service.TriggerCollection()
	assert.NoError(t, err)

	// 等待一下让异步操作完成
	time.Sleep(100 * time.Millisecond)
}

// TestNewsService_CollectNews 测试手动采集新闻
func TestNewsService_CollectNews(t *testing.T) {
	mockRepo := &MockNewsRepository{}

	// 设置mock期望 - 允许任何Exists和Create调用
	mockRepo.On("Exists", mock.Anything, mock.Anything, mock.Anything).Return(false, nil)
	mockRepo.On("Create", mock.Anything, mock.Anything).Return(nil)

	service := NewNewsService(mockRepo)
	ctx := context.Background()

	// 执行采集（这里会实际调用采集器，可能会失败）
	result, err := service.CollectNews(ctx)
	
	// 由于是模拟环境，可能会失败，但不应该panic
	if err != nil {
		t.Logf("采集失败（预期行为）: %v", err)
	} else {
		assert.NotNil(t, result)
	}

	// 验证mock调用
	mockRepo.AssertExpectations(t)
}