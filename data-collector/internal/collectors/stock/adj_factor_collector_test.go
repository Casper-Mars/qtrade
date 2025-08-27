package stock

import (
	"context"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"

	"data-collector/internal/models"
	"data-collector/pkg/client"
)

// MockAdjFactorTushareClient 模拟TushareClient
type MockAdjFactorTushareClient struct {
	mock.Mock
}

func (m *MockAdjFactorTushareClient) Call(ctx context.Context, apiName string, params map[string]interface{}, fields string) (*client.TushareResponse, error) {
	args := m.Called(ctx, apiName, params, fields)
	return args.Get(0).(*client.TushareResponse), args.Error(1)
}

func (m *MockAdjFactorTushareClient) CallWithRetry(ctx context.Context, apiName string, params map[string]interface{}, fields string) (*client.TushareResponse, error) {
	args := m.Called(ctx, apiName, params, fields)
	return args.Get(0).(*client.TushareResponse), args.Error(1)
}

func (m *MockAdjFactorTushareClient) Close() {
	m.Called()
}

// MockAdjFactorStockRepository 模拟StockRepository
type MockAdjFactorStockRepository struct {
	mock.Mock
}

func (m *MockAdjFactorStockRepository) CreateStock(ctx context.Context, stock *models.StockBasic) error {
	args := m.Called(ctx, stock)
	return args.Error(0)
}

func (m *MockAdjFactorStockRepository) GetStockBySymbol(ctx context.Context, symbol string) (*models.StockBasic, error) {
	args := m.Called(ctx, symbol)
	return args.Get(0).(*models.StockBasic), args.Error(1)
}

func (m *MockAdjFactorStockRepository) GetStockByTSCode(ctx context.Context, tsCode string) (*models.StockBasic, error) {
	args := m.Called(ctx, tsCode)
	return args.Get(0).(*models.StockBasic), args.Error(1)
}

func (m *MockAdjFactorStockRepository) UpdateStock(ctx context.Context, stock *models.StockBasic) error {
	args := m.Called(ctx, stock)
	return args.Error(0)
}

func (m *MockAdjFactorStockRepository) DeleteStock(ctx context.Context, symbol string) error {
	args := m.Called(ctx, symbol)
	return args.Error(0)
}

func (m *MockAdjFactorStockRepository) ListStocks(ctx context.Context, limit, offset int) ([]*models.StockBasic, error) {
	args := m.Called(ctx, limit, offset)
	return args.Get(0).([]*models.StockBasic), args.Error(1)
}

func (m *MockAdjFactorStockRepository) BatchCreateStocks(ctx context.Context, stocks []*models.StockBasic) error {
	args := m.Called(ctx, stocks)
	return args.Error(0)
}

func (m *MockAdjFactorStockRepository) CreateStockQuote(ctx context.Context, quote *models.StockQuote) error {
	args := m.Called(ctx, quote)
	return args.Error(0)
}

func (m *MockAdjFactorStockRepository) GetStockQuote(ctx context.Context, symbol string, tradeDate time.Time) (*models.StockQuote, error) {
	args := m.Called(ctx, symbol, tradeDate)
	return args.Get(0).(*models.StockQuote), args.Error(1)
}

func (m *MockAdjFactorStockRepository) GetStockQuotesBySymbol(ctx context.Context, symbol string, startDate, endDate time.Time) ([]*models.StockQuote, error) {
	args := m.Called(ctx, symbol, startDate, endDate)
	return args.Get(0).([]*models.StockQuote), args.Error(1)
}

func (m *MockAdjFactorStockRepository) GetStockQuotesByDate(ctx context.Context, tradeDate time.Time) ([]*models.StockQuote, error) {
	args := m.Called(ctx, tradeDate)
	return args.Get(0).([]*models.StockQuote), args.Error(1)
}

func (m *MockAdjFactorStockRepository) UpdateStockQuote(ctx context.Context, quote *models.StockQuote) error {
	args := m.Called(ctx, quote)
	return args.Error(0)
}

func (m *MockAdjFactorStockRepository) DeleteStockQuote(ctx context.Context, symbol string, tradeDate time.Time) error {
	args := m.Called(ctx, symbol, tradeDate)
	return args.Error(0)
}

func (m *MockAdjFactorStockRepository) BatchCreateStockQuotes(ctx context.Context, quotes []*models.StockQuote) error {
	args := m.Called(ctx, quotes)
	return args.Error(0)
}

func (m *MockAdjFactorStockRepository) CreateAdjFactor(ctx context.Context, adjFactor *models.AdjFactor) error {
	args := m.Called(ctx, adjFactor)
	return args.Error(0)
}

func (m *MockAdjFactorStockRepository) GetAdjFactor(ctx context.Context, tsCode string, tradeDate time.Time) (*models.AdjFactor, error) {
	args := m.Called(ctx, tsCode, tradeDate)
	return args.Get(0).(*models.AdjFactor), args.Error(1)
}

func (m *MockAdjFactorStockRepository) GetAdjFactorsByTSCode(ctx context.Context, tsCode string, startDate, endDate time.Time) ([]*models.AdjFactor, error) {
	args := m.Called(ctx, tsCode, startDate, endDate)
	return args.Get(0).([]*models.AdjFactor), args.Error(1)
}

func (m *MockAdjFactorStockRepository) UpdateAdjFactor(ctx context.Context, adjFactor *models.AdjFactor) error {
	args := m.Called(ctx, adjFactor)
	return args.Error(0)
}

func (m *MockAdjFactorStockRepository) DeleteAdjFactor(ctx context.Context, tsCode string, tradeDate time.Time) error {
	args := m.Called(ctx, tsCode, tradeDate)
	return args.Error(0)
}

func (m *MockAdjFactorStockRepository) BatchCreateAdjFactors(ctx context.Context, adjFactors []*models.AdjFactor) error {
	args := m.Called(ctx, adjFactors)
	return args.Error(0)
}

func TestNewAdjFactorCollector(t *testing.T) {
	mockClient := &MockAdjFactorTushareClient{}
	mockRepo := &MockAdjFactorStockRepository{}

	collector := NewAdjFactorCollector(mockClient, mockRepo)

	assert.NotNil(t, collector)
	assert.Equal(t, mockClient, collector.tushareClient)
	assert.Equal(t, mockRepo, collector.stockRepo)
}

func TestAdjFactorCollector_parseAdjFactorData(t *testing.T) {
	mockClient := &MockAdjFactorTushareClient{}
	mockRepo := &MockAdjFactorStockRepository{}
	collector := NewAdjFactorCollector(mockClient, mockRepo)

	// 测试正常数据
	resp := &client.TushareResponse{
		Data: &client.TushareData{
			Fields: []string{"ts_code", "trade_date", "adj_factor"},
			Items: [][]interface{}{
				{"000001.SZ", "20240101", 1.234567},
				{"000002.SZ", "20240101", 2.345678},
			},
		},
	}

	adjFactors, err := collector.parseAdjFactorData(resp)
	assert.NoError(t, err)
	assert.Len(t, adjFactors, 2)

	// 验证第一条数据
	assert.Equal(t, "000001.SZ", adjFactors[0].TSCode)
	assert.Equal(t, "1.234567", adjFactors[0].AdjFactor)
	expectedDate, _ := time.Parse("20060102", "20240101")
	assert.Equal(t, expectedDate, adjFactors[0].TradeDate)

	// 测试空数据
	emptyResp := &client.TushareResponse{
		Data: &client.TushareData{
			Fields: []string{},
			Items:  [][]interface{}{},
		},
	}
	adjFactors, err = collector.parseAdjFactorData(emptyResp)
	assert.NoError(t, err)
	assert.Nil(t, adjFactors)
}

func TestAdjFactorCollector_isValidAdjFactor(t *testing.T) {
	mockClient := &MockAdjFactorTushareClient{}
	mockRepo := &MockAdjFactorStockRepository{}
	collector := NewAdjFactorCollector(mockClient, mockRepo)

	// 测试有效数据
	validAdjFactor := &models.AdjFactor{
		TSCode:    "000001.SZ",
		TradeDate: time.Now().AddDate(0, 0, -1), // 昨天
		AdjFactor: "1.234567",
	}
	assert.True(t, collector.isValidAdjFactor(validAdjFactor))

	// 测试无效数据 - 空股票代码
	invalidAdjFactor1 := &models.AdjFactor{
		TSCode:    "",
		TradeDate: time.Now().AddDate(0, 0, -1),
		AdjFactor: "1.234567",
	}
	assert.False(t, collector.isValidAdjFactor(invalidAdjFactor1))

	// 测试无效数据 - 零时间
	invalidAdjFactor2 := &models.AdjFactor{
		TSCode:    "000001.SZ",
		TradeDate: time.Time{},
		AdjFactor: "1.234567",
	}
	assert.False(t, collector.isValidAdjFactor(invalidAdjFactor2))

	// 测试无效数据 - 复权因子超出范围
	invalidAdjFactor3 := &models.AdjFactor{
		TSCode:    "000001.SZ",
		TradeDate: time.Now().AddDate(0, 0, -1),
		AdjFactor: "101.0", // 超出范围
	}
	assert.False(t, collector.isValidAdjFactor(invalidAdjFactor3))
}

func TestAdjFactorCollector_parseFloatField(t *testing.T) {
	mockClient := &MockAdjFactorTushareClient{}
	mockRepo := &MockAdjFactorStockRepository{}
	collector := NewAdjFactorCollector(mockClient, mockRepo)

	// 测试float64类型
	value1, err1 := collector.parseFloatField(1.234)
	assert.NoError(t, err1)
	assert.Equal(t, 1.234, value1)

	// 测试string类型
	value2, err2 := collector.parseFloatField("2.345")
	assert.NoError(t, err2)
	assert.Equal(t, 2.345, value2)

	// 测试int类型
	value3, err3 := collector.parseFloatField(3)
	assert.NoError(t, err3)
	assert.Equal(t, 3.0, value3)

	// 测试无效类型
	_, err4 := collector.parseFloatField(nil)
	assert.Error(t, err4)
}

func TestAdjFactorCollector_GetCollectorInfo(t *testing.T) {
	mockClient := &MockAdjFactorTushareClient{}
	mockRepo := &MockAdjFactorStockRepository{}
	collector := NewAdjFactorCollector(mockClient, mockRepo)

	info := collector.GetCollectorInfo()

	assert.Equal(t, "复权因子数据采集器", info["name"])
	assert.Equal(t, "采集股票复权因子数据，支持按日期、时间范围和最新数据采集", info["description"])
	assert.Equal(t, "1.0.0", info["version"])
	assert.Contains(t, info, "features")
}