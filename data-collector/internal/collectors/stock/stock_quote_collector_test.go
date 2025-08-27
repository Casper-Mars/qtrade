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

// MockStockRepository 模拟股票仓库
type MockStockRepository struct {
	mock.Mock
}

func (m *MockStockRepository) CreateStock(ctx context.Context, stock *models.StockBasic) error {
	args := m.Called(ctx, stock)
	return args.Error(0)
}

func (m *MockStockRepository) GetStockBySymbol(ctx context.Context, symbol string) (*models.StockBasic, error) {
	args := m.Called(ctx, symbol)
	return args.Get(0).(*models.StockBasic), args.Error(1)
}

func (m *MockStockRepository) GetStockByTSCode(ctx context.Context, tsCode string) (*models.StockBasic, error) {
	args := m.Called(ctx, tsCode)
	return args.Get(0).(*models.StockBasic), args.Error(1)
}

func (m *MockStockRepository) UpdateStock(ctx context.Context, stock *models.StockBasic) error {
	args := m.Called(ctx, stock)
	return args.Error(0)
}

func (m *MockStockRepository) DeleteStock(ctx context.Context, symbol string) error {
	args := m.Called(ctx, symbol)
	return args.Error(0)
}

func (m *MockStockRepository) ListStocks(ctx context.Context, limit, offset int) ([]*models.StockBasic, error) {
	args := m.Called(ctx, limit, offset)
	return args.Get(0).([]*models.StockBasic), args.Error(1)
}

func (m *MockStockRepository) BatchCreateStocks(ctx context.Context, stocks []*models.StockBasic) error {
	args := m.Called(ctx, stocks)
	return args.Error(0)
}

func (m *MockStockRepository) CreateStockQuote(ctx context.Context, quote *models.StockQuote) error {
	args := m.Called(ctx, quote)
	return args.Error(0)
}

func (m *MockStockRepository) GetStockQuote(ctx context.Context, symbol string, tradeDate time.Time) (*models.StockQuote, error) {
	args := m.Called(ctx, symbol, tradeDate)
	return args.Get(0).(*models.StockQuote), args.Error(1)
}

func (m *MockStockRepository) GetStockQuotesBySymbol(ctx context.Context, symbol string, startDate, endDate time.Time) ([]*models.StockQuote, error) {
	args := m.Called(ctx, symbol, startDate, endDate)
	return args.Get(0).([]*models.StockQuote), args.Error(1)
}

func (m *MockStockRepository) GetStockQuotesByDate(ctx context.Context, tradeDate time.Time) ([]*models.StockQuote, error) {
	args := m.Called(ctx, tradeDate)
	return args.Get(0).([]*models.StockQuote), args.Error(1)
}

func (m *MockStockRepository) UpdateStockQuote(ctx context.Context, quote *models.StockQuote) error {
	args := m.Called(ctx, quote)
	return args.Error(0)
}

func (m *MockStockRepository) DeleteStockQuote(ctx context.Context, symbol string, tradeDate time.Time) error {
	args := m.Called(ctx, symbol, tradeDate)
	return args.Error(0)
}

func (m *MockStockRepository) BatchCreateStockQuotes(ctx context.Context, quotes []*models.StockQuote) error {
	args := m.Called(ctx, quotes)
	return args.Error(0)
}

func (m *MockStockRepository) CreateAdjFactor(ctx context.Context, adjFactor *models.AdjFactor) error {
	args := m.Called(ctx, adjFactor)
	return args.Error(0)
}

func (m *MockStockRepository) GetAdjFactor(ctx context.Context, tsCode string, tradeDate time.Time) (*models.AdjFactor, error) {
	args := m.Called(ctx, tsCode, tradeDate)
	return args.Get(0).(*models.AdjFactor), args.Error(1)
}

func (m *MockStockRepository) GetAdjFactorsByTSCode(ctx context.Context, tsCode string, startDate, endDate time.Time) ([]*models.AdjFactor, error) {
	args := m.Called(ctx, tsCode, startDate, endDate)
	return args.Get(0).([]*models.AdjFactor), args.Error(1)
}

func (m *MockStockRepository) UpdateAdjFactor(ctx context.Context, adjFactor *models.AdjFactor) error {
	args := m.Called(ctx, adjFactor)
	return args.Error(0)
}

func (m *MockStockRepository) DeleteAdjFactor(ctx context.Context, tsCode string, tradeDate time.Time) error {
	args := m.Called(ctx, tsCode, tradeDate)
	return args.Error(0)
}

func (m *MockStockRepository) BatchCreateAdjFactors(ctx context.Context, adjFactors []*models.AdjFactor) error {
	args := m.Called(ctx, adjFactors)
	return args.Error(0)
}

// MockTushareClient 模拟Tushare客户端
type MockTushareClient struct {
	mock.Mock
}

func (m *MockTushareClient) Call(ctx context.Context, apiName string, params map[string]interface{}, fields string) (*client.TushareResponse, error) {
	args := m.Called(ctx, apiName, params, fields)
	return args.Get(0).(*client.TushareResponse), args.Error(1)
}

func (m *MockTushareClient) CallWithRetry(ctx context.Context, apiName string, params map[string]interface{}, fields string) (*client.TushareResponse, error) {
	args := m.Called(ctx, apiName, params, fields)
	return args.Get(0).(*client.TushareResponse), args.Error(1)
}

func TestNewStockQuoteCollector(t *testing.T) {
	// 创建真实的TushareClient用于测试
	tushareClient := client.NewTushareClient("test-token", "https://api.tushare.pro")
	mockStockRepo := &MockStockRepository{}

	collector := NewStockQuoteCollector(tushareClient, mockStockRepo)

	assert.NotNil(t, collector)
	assert.Equal(t, tushareClient, collector.tushareClient)
	assert.Equal(t, mockStockRepo, collector.stockRepo)
}

func TestStockQuoteCollector_CollectByDate(t *testing.T) {
	mockTushareClient := &MockTushareClient{}
	mockStockRepo := &MockStockRepository{}
	collector := NewStockQuoteCollector(mockTushareClient, mockStockRepo)

	ctx := context.Background()
	testDate := time.Date(2024, 1, 15, 0, 0, 0, 0, time.UTC)
	symbols := []string{"000001.SZ", "000002.SZ"}

	// 模拟Tushare API响应
	mockResponse := &client.TushareResponse{
		RequestID: "test-request-id",
		Code:      0,
		Msg:       "success",
		Data: &client.TushareData{
			Fields: []string{"ts_code", "trade_date", "open", "high", "low", "close", "pre_close", "change", "pct_chg", "vol", "amount"},
			Items: [][]interface{}{
				{"000001.SZ", "20240115", 10.50, 10.80, 10.30, 10.70, 10.40, 0.30, 2.88, 1000000.0, 10700000.0},
				{"000002.SZ", "20240115", 20.50, 20.80, 20.30, 20.70, 20.40, 0.30, 1.47, 2000000.0, 41400000.0},
			},
		},
	}

	mockTushareClient.On("CallWithRetry", ctx, "daily", mock.AnythingOfType("map[string]interface {}"), mock.AnythingOfType("string")).Return(mockResponse, nil)
	mockStockRepo.On("BatchCreateStockQuotes", ctx, mock.AnythingOfType("[]*models.StockQuote")).Return(nil)

	err := collector.CollectByDate(ctx, testDate, symbols)

	assert.NoError(t, err)
	mockTushareClient.AssertExpectations(t)
	mockStockRepo.AssertExpectations(t)
}

func TestStockQuoteCollector_CollectByDate_NoSymbols(t *testing.T) {
	mockTushareClient := &MockTushareClient{}
	mockStockRepo := &MockStockRepository{}
	collector := NewStockQuoteCollector(mockTushareClient, mockStockRepo)

	ctx := context.Background()
	testDate := time.Date(2024, 1, 15, 0, 0, 0, 0, time.UTC)

	// 模拟获取股票列表
	mockStocks := []*models.StockBasic{
		{Symbol: "000001", TSCode: "000001.SZ", Name: "平安银行"},
		{Symbol: "000002", TSCode: "000002.SZ", Name: "万科A"},
	}
	mockStockRepo.On("ListStocks", ctx, 10000, 0).Return(mockStocks, nil)

	// 模拟Tushare API响应
	mockResponse := &client.TushareResponse{
		RequestID: "test-request-id",
		Code:      0,
		Msg:       "success",
		Data: &client.TushareData{
			Fields: []string{"ts_code", "trade_date", "open", "high", "low", "close", "pre_close", "change", "pct_chg", "vol", "amount"},
			Items: [][]interface{}{
				{"000001.SZ", "20240115", 10.50, 10.80, 10.30, 10.70, 10.40, 0.30, 2.88, 1000000.0, 10700000.0},
				{"000002.SZ", "20240115", 20.50, 20.80, 20.30, 20.70, 20.40, 0.30, 1.47, 2000000.0, 41400000.0},
			},
		},
	}

	mockTushareClient.On("CallWithRetry", ctx, "daily", mock.AnythingOfType("map[string]interface {}"), mock.AnythingOfType("string")).Return(mockResponse, nil)
	mockStockRepo.On("BatchCreateStockQuotes", ctx, mock.AnythingOfType("[]*models.StockQuote")).Return(nil)

	err := collector.CollectByDate(ctx, testDate, nil)

	assert.NoError(t, err)
	mockTushareClient.AssertExpectations(t)
	mockStockRepo.AssertExpectations(t)
}

func TestStockQuoteCollector_parseStockQuoteData(t *testing.T) {
	mockTushareClient := &MockTushareClient{}
	mockStockRepo := &MockStockRepository{}
	collector := NewStockQuoteCollector(mockTushareClient, mockStockRepo)

	// 测试正常数据解析
	data := &client.TushareData{
		Fields: []string{"ts_code", "trade_date", "open", "high", "low", "close", "pre_close", "change", "pct_chg", "vol", "amount"},
		Items: [][]interface{}{
			{"000001.SZ", "20240115", 10.50, 10.80, 10.30, 10.70, 10.40, 0.30, 2.88, 1000000.0, 10700000.0},
			{"000002.SZ", "20240115", 20.50, 20.80, 20.30, 20.70, 20.40, 0.30, 1.47, 2000000.0, 41400000.0},
		},
	}

	quotes, err := collector.parseStockQuoteData(data)

	assert.NoError(t, err)
	assert.Len(t, quotes, 2)

	// 验证第一条数据
	assert.Equal(t, "000001", quotes[0].Symbol)
	assert.Equal(t, "10.5", quotes[0].Open)
	assert.Equal(t, "10.8", quotes[0].High)
	assert.Equal(t, "10.3", quotes[0].Low)
	assert.Equal(t, "10.7", quotes[0].Close)
	assert.Equal(t, time.Date(2024, 1, 15, 0, 0, 0, 0, time.UTC), quotes[0].TradeDate)

	// 验证第二条数据
	assert.Equal(t, "000002", quotes[1].Symbol)
	assert.Equal(t, "20.5", quotes[1].Open)
	assert.Equal(t, "20.8", quotes[1].High)
	assert.Equal(t, "20.3", quotes[1].Low)
	assert.Equal(t, "20.7", quotes[1].Close)
}

func TestStockQuoteCollector_parseStockQuoteData_EmptyData(t *testing.T) {
	mockTushareClient := &MockTushareClient{}
	mockStockRepo := &MockStockRepository{}
	collector := NewStockQuoteCollector(mockTushareClient, mockStockRepo)

	// 测试空数据
	data := &client.TushareData{
		Fields: []string{},
		Items:  [][]interface{}{},
	}

	quotes, err := collector.parseStockQuoteData(data)

	assert.Error(t, err)
	assert.Nil(t, quotes)
	assert.Contains(t, err.Error(), "数据为空")
}

func TestStockQuoteCollector_parseStockQuoteData_MissingFields(t *testing.T) {
	mockTushareClient := &MockTushareClient{}
	mockStockRepo := &MockStockRepository{}
	collector := NewStockQuoteCollector(mockTushareClient, mockStockRepo)

	// 测试缺少必需字段
	data := &client.TushareData{
		Fields: []string{"ts_code", "trade_date"}, // 缺少价格字段
		Items: [][]interface{}{
			{"000001.SZ", "20240115"},
		},
	}

	quotes, err := collector.parseStockQuoteData(data)

	assert.Error(t, err)
	assert.Nil(t, quotes)
	assert.Contains(t, err.Error(), "缺少必需字段")
}

func TestStockQuoteCollector_isValidQuote(t *testing.T) {
	mockTushareClient := &MockTushareClient{}
	mockStockRepo := &MockStockRepository{}
	collector := NewStockQuoteCollector(mockTushareClient, mockStockRepo)

	// 测试有效数据
	validQuote := &models.StockQuote{
		Symbol:    "000001",
		TradeDate: time.Date(2024, 1, 15, 0, 0, 0, 0, time.UTC),
		Open:      "10.50",
		High:      "10.80",
		Low:       "10.30",
		Close:     "10.70",
	}

	assert.True(t, collector.isValidQuote(validQuote))

	// 测试无效数据 - 空股票代码
	invalidQuote1 := &models.StockQuote{
		Symbol:    "",
		TradeDate: time.Date(2024, 1, 15, 0, 0, 0, 0, time.UTC),
		Open:      "10.50",
		High:      "10.80",
		Low:       "10.30",
		Close:     "10.70",
	}

	assert.False(t, collector.isValidQuote(invalidQuote1))

	// 测试无效数据 - 零时间
	invalidQuote2 := &models.StockQuote{
		Symbol:    "000001",
		TradeDate: time.Time{},
		Open:      "10.50",
		High:      "10.80",
		Low:       "10.30",
		Close:     "10.70",
	}

	assert.False(t, collector.isValidQuote(invalidQuote2))

	// 测试无效数据 - 价格逻辑错误（最高价小于最低价）
	invalidQuote3 := &models.StockQuote{
		Symbol:    "000001",
		TradeDate: time.Date(2024, 1, 15, 0, 0, 0, 0, time.UTC),
		Open:      "10.50",
		High:      "10.30", // 最高价小于最低价
		Low:       "10.80",
		Close:     "10.70",
	}

	assert.False(t, collector.isValidQuote(invalidQuote3))

	// 测试无效数据 - 负价格
	invalidQuote4 := &models.StockQuote{
		Symbol:    "000001",
		TradeDate: time.Date(2024, 1, 15, 0, 0, 0, 0, time.UTC),
		Open:      "-10.50", // 负价格
		High:      "10.80",
		Low:       "10.30",
		Close:     "10.70",
	}

	assert.False(t, collector.isValidQuote(invalidQuote4))
}

func TestStockQuoteCollector_parseFloatField(t *testing.T) {
	mockTushareClient := &MockTushareClient{}
	mockStockRepo := &MockStockRepository{}
	collector := NewStockQuoteCollector(mockTushareClient, mockStockRepo)

	// 测试float64类型
	result1 := collector.parseFloatField(10.50)
	assert.Equal(t, "10.5", result1)

	// 测试string类型
	result2 := collector.parseFloatField("20.30")
	assert.Equal(t, "20.30", result2)

	// 测试空字符串
	result3 := collector.parseFloatField("")
	assert.Equal(t, "0", result3)

	// 测试nil值
	result4 := collector.parseFloatField(nil)
	assert.Equal(t, "0", result4)

	// 测试其他类型
	result5 := collector.parseFloatField(123)
	assert.Equal(t, "123", result5)
}

func TestStockQuoteCollector_getLatestTradeDate(t *testing.T) {
	mockTushareClient := &MockTushareClient{}
	mockStockRepo := &MockStockRepository{}
	collector := NewStockQuoteCollector(mockTushareClient, mockStockRepo)

	latestDate := collector.getLatestTradeDate()

	// 验证返回的日期不是周末
	assert.NotEqual(t, time.Saturday, latestDate.Weekday())
	assert.NotEqual(t, time.Sunday, latestDate.Weekday())

	// 验证时间是UTC零点
	assert.Equal(t, 0, latestDate.Hour())
	assert.Equal(t, 0, latestDate.Minute())
	assert.Equal(t, 0, latestDate.Second())
	assert.Equal(t, time.UTC, latestDate.Location())
}

func TestStockQuoteCollector_GetCollectorInfo(t *testing.T) {
	mockTushareClient := &MockTushareClient{}
	mockStockRepo := &MockStockRepository{}
	collector := NewStockQuoteCollector(mockTushareClient, mockStockRepo)

	info := collector.GetCollectorInfo()

	assert.Equal(t, "StockQuoteCollector", info["name"])
	assert.Equal(t, "股票行情数据采集器", info["description"])
	assert.Equal(t, "1.0.0", info["version"])
	assert.Equal(t, "Tushare", info["data_source"])
	assert.Equal(t, "daily", info["api_name"])
}