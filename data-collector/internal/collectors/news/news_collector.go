package news

import (
	"context"
	"encoding/json"
	"fmt"
	"regexp"
	"strings"
	"time"

	"data-collector/internal/models"
	"data-collector/internal/storage"
	"data-collector/pkg/logger"

	"github.com/gocolly/colly/v2"
	"github.com/gocolly/colly/v2/debug"
	"go.mongodb.org/mongo-driver/bson/primitive"
)

// NewsCollector 新闻采集器接口
type NewsCollector interface {
	// 采集财联社快讯
	CollectCLSNews(ctx context.Context) (*CollectResult, error)
	// 获取采集器信息
	GetCollectorInfo() map[string]interface{}
}

// CLSNewsCollector 财联社新闻采集器
type CLSNewsCollector struct {
	newsRepo  storage.NewsRepository
	collector *colly.Collector
}

// CLSNewsItem 财联社新闻项目结构
type CLSNewsItem struct {
	ID           int    `json:"id"`
	Title        string `json:"title"`
	Content      string `json:"content"`
	Brief        string `json:"brief"`
	Ctime        int64  `json:"ctime"`
	ModifiedTime int64  `json:"modified_time"`
	ShareURL     string `json:"shareurl"`
	StockList    []struct {
		Code string `json:"code"`
		Name string `json:"name"`
	} `json:"stock_list"`
}

// CollectResult 采集结果
type CollectResult struct {
	Success     bool           `json:"success"`
	Message     string         `json:"message"`
	Total       int            `json:"total"`
	Processed   int            `json:"processed"`
	Skipped     int            `json:"skipped"`
	Errors      int            `json:"errors"`
	StartTime   time.Time      `json:"start_time"`
	EndTime     time.Time      `json:"end_time"`
	Duration    string         `json:"duration"`
	NewsList    []*models.News `json:"news_list"` // 添加新闻数据列表
}

// NewCLSNewsCollector 创建财联社新闻采集器
func NewCLSNewsCollector(newsRepo storage.NewsRepository) NewsCollector {
	c := colly.NewCollector(
		colly.Debugger(&debug.LogDebugger{}),
		colly.UserAgent("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
	)

	// 设置请求延迟
	c.Limit(&colly.LimitRule{
		DomainGlob:  "*cls.cn*",
		Parallelism: 1,
		Delay:       3 * time.Second,
	})

	// 设置超时
	c.SetRequestTimeout(30 * time.Second)

	// 设置请求头，模拟真实浏览器
	c.OnRequest(func(r *colly.Request) {
		r.Headers.Set("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7")
		r.Headers.Set("Accept-Language", "zh-CN,zh;q=0.9,en;q=0.8")
		r.Headers.Set("Accept-Encoding", "gzip, deflate, br")
		r.Headers.Set("Cache-Control", "no-cache")
		r.Headers.Set("Pragma", "no-cache")
		r.Headers.Set("Sec-Ch-Ua", `"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"`)
		r.Headers.Set("Sec-Ch-Ua-Mobile", "?0")
		r.Headers.Set("Sec-Ch-Ua-Platform", `"macOS"`)
		r.Headers.Set("Sec-Fetch-Dest", "document")
		r.Headers.Set("Sec-Fetch-Mode", "navigate")
		r.Headers.Set("Sec-Fetch-Site", "none")
		r.Headers.Set("Sec-Fetch-User", "?1")
		r.Headers.Set("Upgrade-Insecure-Requests", "1")
	})

	return &CLSNewsCollector{
		newsRepo:  newsRepo,
		collector: c,
	}
}

// CollectCLSNews 采集财联社快讯
func (c *CLSNewsCollector) CollectCLSNews(ctx context.Context) (*CollectResult, error) {
	result := &CollectResult{
		StartTime: time.Now(),
		Success:   false,
	}

	// 清除访问记录，允许重复访问
	c.collector.OnRequest(func(r *colly.Request) {
		r.Headers.Set("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7")
		r.Headers.Set("Accept-Language", "zh-CN,zh;q=0.9,en;q=0.8")
		r.Headers.Set("Accept-Encoding", "gzip, deflate, br")
		r.Headers.Set("Cache-Control", "no-cache")
		r.Headers.Set("Pragma", "no-cache")
		r.Headers.Set("Sec-Ch-Ua", `"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"`)
		r.Headers.Set("Sec-Ch-Ua-Mobile", "?0")
		r.Headers.Set("Sec-Ch-Ua-Platform", `"macOS"`)
		r.Headers.Set("Sec-Fetch-Dest", "document")
		r.Headers.Set("Sec-Fetch-Mode", "navigate")
		r.Headers.Set("Sec-Fetch-Site", "none")
		r.Headers.Set("Sec-Fetch-User", "?1")
		r.Headers.Set("Upgrade-Insecure-Requests", "1")
	})

	var newsList []*models.News
	var errors []string

	// 设置HTML解析回调 - 解析页面中的JSON数据
	c.collector.OnHTML("html", func(e *colly.HTMLElement) {
		// 获取页面HTML内容
		htmlContent, _ := e.DOM.Html()
		
		// 提取JSON数据 - 使用字符串搜索和括号匹配
        // 财联社的新闻数据以JSON格式嵌入在HTML中
        var matches []string
        
        // 查找所有包含author_extends的JSON对象起始位置
        searchStr := `{"author_extends":`
        startIndex := 0
        
        for {
            index := strings.Index(htmlContent[startIndex:], searchStr)
            if index == -1 {
                break
            }
            
            actualIndex := startIndex + index
            // 从这个位置开始，找到匹配的结束大括号
            jsonStr := extractJSONObject(htmlContent, actualIndex)
            if jsonStr != "" {
                matches = append(matches, jsonStr)
            }
            
            startIndex = actualIndex + 1
        }
		
		logger.Infof("找到 %d 条JSON数据", len(matches))
		
		for _, match := range matches {
			var newsItem CLSNewsItem
			if err := json.Unmarshal([]byte(match), &newsItem); err != nil {
				logger.Errorf("解析JSON失败: %v, JSON: %s", err, match[:100])
				continue
			}
			
			// 跳过无效数据
			if newsItem.ID == 0 || (newsItem.Title == "" && newsItem.Content == "") {
				continue
			}
			
			news := &models.News{
				ID:        primitive.NewObjectID(),
				Source:    "财联社",
				Title:     strings.TrimSpace(newsItem.Title),
				Content:   strings.TrimSpace(newsItem.Content),
				CreatedAt: time.Now(),
				UpdatedAt: time.Now(),
			}
			
			// 如果没有标题，使用brief或content的前50个字符
			if news.Title == "" {
				if newsItem.Brief != "" {
					news.Title = strings.TrimSpace(newsItem.Brief)
					if len(news.Title) > 50 {
						news.Title = news.Title[:50] + "..."
					}
				} else if len(news.Content) > 0 {
					news.Title = news.Content
					if len(news.Title) > 50 {
						news.Title = news.Title[:50] + "..."
					}
				}
			}
			
			// 解析发布时间
			if newsItem.Ctime > 0 {
				news.PublishTime = time.Unix(newsItem.Ctime, 0)
			} else if newsItem.ModifiedTime > 0 {
				news.PublishTime = time.Unix(newsItem.ModifiedTime, 0)
			} else {
				news.PublishTime = time.Now()
			}
			
			// 设置URL
			if newsItem.ShareURL != "" {
				news.URL = newsItem.ShareURL
			} else {
				news.URL = fmt.Sprintf("https://www.cls.cn/detail/%d", newsItem.ID)
			}
			
			// 提取关联股票
			for _, stock := range newsItem.StockList {
				if stock.Code != "" && stock.Name != "" {
					news.RelatedStocks = append(news.RelatedStocks, models.RelatedStock{
						Code: stock.Code,
						Name: stock.Name,
					})
				}
			}
			
			// 从文本中提取更多关联股票
			additionalStocks := c.extractRelatedStocks(news.Title + " " + news.Content)
			news.RelatedStocks = append(news.RelatedStocks, additionalStocks...)
			
			// 提取关联行业
			news.RelatedIndustries = c.extractRelatedIndustries(news.Title + " " + news.Content)
			
			// 验证数据完整性
			if c.isValidNews(news) {
				newsList = append(newsList, news)
			} else {
				logger.Warnf("无效的新闻数据: ID=%d, 标题=%s, 内容长度=%d, 来源=%s, 发布时间=%v",
			news.ID, news.Title, len(news.Content), news.Source, news.PublishTime)
				errors = append(errors, fmt.Sprintf("无效的新闻数据: ID=%d, 标题=%s", newsItem.ID, news.Title))
			}
		}
	})

	// 设置错误处理
	c.collector.OnError(func(r *colly.Response, err error) {
		errors = append(errors, fmt.Sprintf("请求失败: %s, error: %v", r.Request.URL, err))
	})

	// 清除访问记录，允许重复访问同一URL
	c.collector.AllowURLRevisit = true

	// 访问财联社快讯页面
	err := c.collector.Visit("https://www.cls.cn/telegraph")
	if err != nil {
		result.Message = fmt.Sprintf("访问财联社快讯页面失败: %v", err)
		result.EndTime = time.Now()
		result.Duration = result.EndTime.Sub(result.StartTime).String()
		return result, err
	}

	// 等待所有请求完成
	c.collector.Wait()

	// 统计结果
	result.Total = len(newsList)
	result.Errors = len(errors)
	result.NewsList = newsList // 将新闻数据添加到结果中

	// 保存新闻数据
	for _, news := range newsList {
		// 检查是否已存在
		exists, err := c.newsRepo.Exists(ctx, news.Title, news.Content)
		if err != nil {
			logger.Errorf("检查新闻是否存在失败: %v", err)
			result.Errors++
			continue
		}

		if exists {
			result.Skipped++
			continue
		}

		// 保存新闻
		if err := c.newsRepo.Create(ctx, news); err != nil {
			logger.Errorf("保存新闻失败: %v", err)
			result.Errors++
		} else {
			result.Processed++
		}
	}

	result.EndTime = time.Now()
	result.Duration = result.EndTime.Sub(result.StartTime).String()
	result.Success = result.Errors == 0 || result.Processed > 0
	result.Message = fmt.Sprintf("采集完成: 总计%d条, 处理%d条, 跳过%d条, 错误%d条", 
		result.Total, result.Processed, result.Skipped, result.Errors)

	return result, nil
}

// parsePublishTime 解析发布时间
func (c *CLSNewsCollector) parsePublishTime(timeStr string) (time.Time, error) {
	// 财联社时间格式通常为: "12:34" 或 "昨天 12:34" 或 "01-15 12:34"
	now := time.Now()
	
	// 处理 "12:34" 格式（今天）
	if matched, _ := regexp.MatchString(`^\d{2}:\d{2}$`, timeStr); matched {
		timeToday, err := time.Parse("15:04", timeStr)
		if err != nil {
			return time.Time{}, err
		}
		return time.Date(now.Year(), now.Month(), now.Day(), 
			timeToday.Hour(), timeToday.Minute(), 0, 0, now.Location()), nil
	}

	// 处理 "昨天 12:34" 格式
	if strings.Contains(timeStr, "昨天") {
		timePart := strings.TrimSpace(strings.Replace(timeStr, "昨天", "", 1))
		timeYesterday, err := time.Parse("15:04", timePart)
		if err != nil {
			return time.Time{}, err
		}
		yesterday := now.AddDate(0, 0, -1)
		return time.Date(yesterday.Year(), yesterday.Month(), yesterday.Day(), 
			timeYesterday.Hour(), timeYesterday.Minute(), 0, 0, now.Location()), nil
	}

	// 处理 "01-15 12:34" 格式
	if matched, _ := regexp.MatchString(`^\d{2}-\d{2} \d{2}:\d{2}$`, timeStr); matched {
		timeWithDate, err := time.Parse("01-02 15:04", timeStr)
		if err != nil {
			return time.Time{}, err
		}
		return time.Date(now.Year(), timeWithDate.Month(), timeWithDate.Day(), 
			timeWithDate.Hour(), timeWithDate.Minute(), 0, 0, now.Location()), nil
	}

	// 默认返回当前时间
	return now, nil
}

// extractRelatedStocks 提取关联股票
func (c *CLSNewsCollector) extractRelatedStocks(text string) []models.RelatedStock {
	var stocks []models.RelatedStock
	
	// 匹配股票代码模式: 6位数字 或 带括号的股票代码
	stockPattern := regexp.MustCompile(`([0-9]{6})|\(([0-9]{6})\)`)
	matches := stockPattern.FindAllStringSubmatch(text, -1)
	
	for _, match := range matches {
		code := ""
		if match[1] != "" {
			code = match[1]
		} else if match[2] != "" {
			code = match[2]
		}
		
		if code != "" {
			// 根据代码前缀判断交易所
			exchange := ""
			if strings.HasPrefix(code, "6") {
				exchange = "SH" // 上交所
			} else if strings.HasPrefix(code, "0") || strings.HasPrefix(code, "3") {
				exchange = "SZ" // 深交所
			}
			
			if exchange != "" {
				stocks = append(stocks, models.RelatedStock{
					Code: code,
					Name: "", // 暂时为空，后续可通过股票代码查询获取
				})
			}
		}
	}
	
	return stocks
}

// extractRelatedIndustries 提取关联行业
func (c *CLSNewsCollector) extractRelatedIndustries(text string) []string {
	var industries []string
	
	// 常见行业关键词
	industryKeywords := map[string]string{
		"银行":     "银行",
		"保险":     "保险",
		"证券":     "证券",
		"房地产":    "房地产",
		"汽车":     "汽车",
		"钢铁":     "钢铁",
		"煤炭":     "煤炭",
		"有色金属":   "有色金属",
		"化工":     "化工",
		"石油":     "石油石化",
		"电力":     "电力",
		"医药":     "医药生物",
		"食品":     "食品饮料",
		"纺织":     "纺织服装",
		"电子":     "电子",
		"计算机":    "计算机",
		"通信":     "通信",
		"传媒":     "传媒",
		"军工":     "国防军工",
		"航空":     "交通运输",
		"物流":     "交通运输",
		"建筑":     "建筑装饰",
		"机械":     "机械设备",
		"农业":     "农林牧渔",
		"旅游":     "休闲服务",
		"零售":     "商业贸易",
		"环保":     "环保",
		"新能源":    "电力设备",
		"光伏":     "电力设备",
		"风电":     "电力设备",
	}
	
	for keyword, industry := range industryKeywords {
		if strings.Contains(text, keyword) {
			// 避免重复添加
			found := false
			for _, existing := range industries {
				if existing == industry {
					found = true
					break
				}
			}
			if !found {
				industries = append(industries, industry)
			}
		}
	}
	
	return industries
}

// isValidNews 验证新闻数据有效性
func (c *CLSNewsCollector) isValidNews(news *models.News) bool {
	if news == nil {
		return false
	}
	
	// 标题不能为空且长度合理
	if strings.TrimSpace(news.Title) == "" || len(news.Title) > 200 {
		return false
	}
	
	// 内容不能为空
	if strings.TrimSpace(news.Content) == "" {
		return false
	}
	
	// 发布时间不能为零值
	if news.PublishTime.IsZero() {
		return false
	}
	
	// 来源不能为空
	if strings.TrimSpace(news.Source) == "" {
		return false
	}
	
	return true
}

// GetCollectorInfo 获取采集器信息
func (c *CLSNewsCollector) GetCollectorInfo() map[string]interface{} {
	return map[string]interface{}{
		"name":        "财联社快讯采集器",
		"description": "采集财联社主页快讯数据，包括标题、内容、发布时间、关联股票和行业信息",
		"source":      "https://www.cls.cn/telegraph",
		"frequency":   "每10分钟采集一次",
		"data_type":   "财经快讯",
		"features": []string{
			"快讯标题和内容提取",
			"发布时间解析",
			"关联股票代码识别",
			"行业关键词提取",
			"数据去重处理",
			"反爬虫策略",
		},
	}
}

// extractJSONObject 从指定位置提取完整的JSON对象
func extractJSONObject(content string, startIndex int) string {
	if startIndex >= len(content) || content[startIndex] != '{' {
		return ""
	}
	
	braceCount := 0
	inQuotes := false
	escaped := false
	
	for i := startIndex; i < len(content); i++ {
		char := content[i]
		
		if escaped {
			escaped = false
			continue
		}
		
		if char == '\\' {
			escaped = true
			continue
		}
		
		if char == '"' {
			inQuotes = !inQuotes
			continue
		}
		
		if !inQuotes {
			if char == '{' {
				braceCount++
			} else if char == '}' {
				braceCount--
				if braceCount == 0 {
					return content[startIndex : i+1]
				}
			}
		}
	}
	
	return ""
}