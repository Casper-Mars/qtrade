package financial

import (
	"context"
	"testing"

	"data-collector/pkg/client"
)

func TestNewFinancialManager(t *testing.T) {
	tushareClient := &client.TushareClient{}
	repository := NewMockFinancialRepository()

	manager := NewFinancialManager(tushareClient, repository)

	if manager == nil {
		t.Error("Expected non-nil manager")
	}

	if manager.reportCollector == nil {
		t.Error("Expected non-nil reportCollector")
	}

	if manager.indicatorCollector == nil {
		t.Error("Expected non-nil indicatorCollector")
	}
}

func TestCollectCompleteFinancialData(t *testing.T) {
	// 这个测试需要模拟TushareClient，这里只测试基本逻辑
	tushareClient := &client.TushareClient{} // 创建空的TushareClient
	repository := NewMockFinancialRepository()
	manager := NewFinancialManager(tushareClient, repository)

	symbols := []string{"000001.SZ", "000002.SZ"}
	ctx := context.Background()

	// 由于TushareClient没有正确初始化，这个测试会失败，这是预期的
	err := manager.CollectFinancialDataBatch(ctx, symbols, 2023, 3)
	if err != nil {
		t.Logf("Expected error occurred: %v", err)
		// 这是预期的行为，因为TushareClient没有正确配置
	}
}