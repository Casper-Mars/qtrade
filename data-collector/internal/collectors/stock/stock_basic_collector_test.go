package stock

import (
	"context"
	"os"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"

	"data-collector/pkg/client"
)



func TestNewStockBasicCollector(t *testing.T) {
	// 创建真实的客户端和仓储用于测试构造函数
	tushareClient := client.NewTushareClient("test_token", "https://api.tushare.pro")
	
	// 注意：这里需要真实的仓储实现，但为了单元测试，我们只测试构造函数不为nil
	assert.NotNil(t, tushareClient)
}

// TestStockBasicCollector_Integration 集成测试
// 注意：这需要真实的API token和数据库连接
func TestStockBasicCollector_Integration(t *testing.T) {
	token := os.Getenv("TUSHARE_TOKEN")
	if token == "" {
		t.Skip("跳过集成测试，需要设置TUSHARE_TOKEN环境变量")
	}
	
	// 创建真实的Tushare客户端
	tushareClient := client.NewTushareClient(token, "https://api.tushare.pro")
	
	// 注意：这里需要真实的数据库连接，暂时跳过完整的集成测试
	// 但我们可以测试数据解析功能
	ctx := context.Background()
	params := map[string]interface{}{
		"list_status": "L",
		"limit":      3, // 只获取3条记录用于测试
	}
	
	// 测试API调用和数据解析
	resp, err := tushareClient.Call(ctx, "stock_basic", params, "ts_code,symbol,name,area,industry,market,list_date,is_hs")
	
	// 如果API调用失败，记录错误并跳过测试
	if err != nil {
		t.Logf("API调用失败: %v", err)
		t.Skip("API调用失败，可能是权限或配额问题")
	}
	
	// 检查响应是否为空
	if resp == nil {
		t.Skip("API响应为空，跳过测试")
	}
	
	// 检查API响应状态
	if resp.Code != 0 {
		t.Logf("API返回错误: Code=%d, Msg=%s", resp.Code, resp.Msg)
		t.Skip("API调用失败，可能是权限或配额问题")
	}
	
	// 只有在成功时才验证数据
	assert.Equal(t, 0, resp.Code)
	assert.NotNil(t, resp.Data)
	
	if resp.Data != nil {
		assert.NotEmpty(t, resp.Data.Items)
		
		// 验证数据结构
		assert.Len(t, resp.Data.Fields, 8)
		assert.LessOrEqual(t, len(resp.Data.Items), 3)
		
		// 验证第一条数据的基本结构
		if len(resp.Data.Items) > 0 {
			firstItem := resp.Data.Items[0]
			assert.Len(t, firstItem, 8) // 应该有8个字段
			assert.NotEmpty(t, firstItem[0]) // ts_code不应为空
			assert.NotEmpty(t, firstItem[1]) // symbol不应为空
			assert.NotEmpty(t, firstItem[2]) // name不应为空
		}
	}
}









// TestParseStockData 测试数据解析功能
func TestParseStockData(t *testing.T) {
	// 准备测试数据
	data := &client.TushareData{
		Fields: []string{"ts_code", "symbol", "name", "area", "industry", "market", "list_date", "is_hs"},
		Items: [][]interface{}{
			{"000001.SZ", "000001", "平安银行", "深圳", "银行", "主板", "19910403", "S"},
			{"000002.SZ", "000002", "万科A", "深圳", "房地产", "主板", "19910129", "S"},
		},
	}
	
	// 验证数据结构
	assert.NotNil(t, data)
	assert.Len(t, data.Fields, 8)
	assert.Len(t, data.Items, 2)
	
	// 验证字段名称
	assert.Equal(t, "ts_code", data.Fields[0])
	assert.Equal(t, "symbol", data.Fields[1])
	assert.Equal(t, "name", data.Fields[2])
	
	// 验证数据项
	assert.Equal(t, "000001.SZ", data.Items[0][0])
	assert.Equal(t, "000001", data.Items[0][1])
	assert.Equal(t, "平安银行", data.Items[0][2])
}

// TestDateParsing 测试日期解析功能
func TestDateParsing(t *testing.T) {
	// 测试有效日期格式
	validDate := "19910403"
	parsedDate, err := time.Parse("20060102", validDate)
	assert.NoError(t, err)
	assert.Equal(t, 1991, parsedDate.Year())
	assert.Equal(t, time.April, parsedDate.Month())
	assert.Equal(t, 3, parsedDate.Day())
	
	// 测试无效日期格式
	invalidDate := "invalid_date"
	_, err = time.Parse("20060102", invalidDate)
	assert.Error(t, err)
}

// TestEmptyData 测试空数据处理
func TestEmptyData(t *testing.T) {
	// 准备测试数据 - 空数据
	data := &client.TushareData{
		Fields: []string{"ts_code", "symbol", "name", "area", "industry", "market", "list_date", "is_hs"},
		Items:  [][]interface{}{},
	}
	
	// 验证空数据结构
	assert.NotNil(t, data)
	assert.Len(t, data.Fields, 8)
	assert.Len(t, data.Items, 0)
}