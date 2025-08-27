package news

import (
	"context"
	"regexp"
	"strings"
	"unicode"

	"data-collector/internal/models"
	"data-collector/pkg/logger"
)

// NewsCleaner 新闻数据清洗器接口
type NewsCleaner interface {
	// CleanNews 清洗单条新闻数据
	CleanNews(ctx context.Context, news *models.News) (*models.News, error)
	// BatchCleanNews 批量清洗新闻数据
	BatchCleanNews(ctx context.Context, newsList []*models.News) ([]*models.News, error)
	// GetCleanerInfo 获取清洗器信息
	GetCleanerInfo() map[string]interface{}
}

// DefaultNewsCleaner 默认新闻清洗器
type DefaultNewsCleaner struct {
	// HTML标签正则表达式
	htmlTagRegex *regexp.Regexp
	// 特殊字符正则表达式
	specialCharRegex *regexp.Regexp
	// 多空格正则表达式
	multiSpaceRegex *regexp.Regexp
	// URL正则表达式
	urlRegex *regexp.Regexp
	// 敏感词列表
	sensitiveWords []string
}

// NewDefaultNewsCleaner 创建默认新闻清洗器
func NewDefaultNewsCleaner() NewsCleaner {
	return &DefaultNewsCleaner{
		htmlTagRegex:     regexp.MustCompile(`<[^>]*>`),
		specialCharRegex: regexp.MustCompile(`[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]`),
		multiSpaceRegex:  regexp.MustCompile(`\s+`),
		urlRegex:         regexp.MustCompile(`https?://[^\s]+`),
		sensitiveWords: []string{
			"广告", "推广", "赞助", "合作", "联系我们",
			"免责声明", "版权声明", "转载", "来源",
		},
	}
}

// CleanNews 清洗单条新闻数据
func (c *DefaultNewsCleaner) CleanNews(ctx context.Context, news *models.News) (*models.News, error) {
	if news == nil {
		return nil, nil
	}

	// 创建清洗后的新闻副本
	cleanedNews := &models.News{
		ID:                news.ID,
		Title:             c.cleanText(news.Title),
		Content:           c.cleanContent(news.Content),
		Source:            news.Source,
		URL:               news.URL,
		PublishTime:       news.PublishTime,
		RelatedStocks:     news.RelatedStocks,
		RelatedIndustries: news.RelatedIndustries,
		CreatedAt:         news.CreatedAt,
		UpdatedAt:         news.UpdatedAt,
	}

	// 验证清洗后的数据
	if !c.isValidCleanedNews(cleanedNews) {
		return nil, nil
	}

	return cleanedNews, nil
}

// BatchCleanNews 批量清洗新闻数据
func (c *DefaultNewsCleaner) BatchCleanNews(ctx context.Context, newsList []*models.News) ([]*models.News, error) {
	if len(newsList) == 0 {
		return []*models.News{}, nil
	}

	cleanedList := make([]*models.News, 0, len(newsList))

	for _, news := range newsList {
		cleanedNews, err := c.CleanNews(ctx, news)
		if err != nil {
			continue // 跳过清洗失败的新闻
		}
		if cleanedNews != nil {
			cleanedList = append(cleanedList, cleanedNews)
		}
	}

	return cleanedList, nil
}

// cleanText 清洗文本内容
func (c *DefaultNewsCleaner) cleanText(text string) string {
	if text == "" {
		return ""
	}

	// 移除HTML标签
	text = c.htmlTagRegex.ReplaceAllString(text, "")

	// 移除特殊控制字符
	text = c.specialCharRegex.ReplaceAllString(text, "")

	// 移除URL链接
	text = c.urlRegex.ReplaceAllString(text, "")

	// 标准化空白字符
	text = c.multiSpaceRegex.ReplaceAllString(text, " ")

	// 去除首尾空白
	text = strings.TrimSpace(text)

	// 移除敏感词相关内容
	text = c.removeSensitiveContent(text)

	return text
}

// cleanContent 清洗新闻内容
func (c *DefaultNewsCleaner) cleanContent(content string) string {
	if content == "" {
		return ""
	}

	// 基础文本清洗
	content = c.cleanText(content)

	// 移除常见的无用段落
	uselessPatterns := []string{
		"本文来源", "责任编辑", "版权声明", "免责声明",
		"更多精彩内容", "关注我们", "扫码关注", "点击阅读",
		"原标题", "编辑", "记者", "通讯员",
	}

	for _, pattern := range uselessPatterns {
		if idx := strings.Index(content, pattern); idx != -1 {
			// 找到无用内容，截取之前的部分
			content = content[:idx]
			break
		}
	}

	// 移除过短的段落（可能是广告或无用信息）
	paragraphs := strings.Split(content, "\n")
	validParagraphs := make([]string, 0, len(paragraphs))

	for _, paragraph := range paragraphs {
		paragraph = strings.TrimSpace(paragraph)
		if len(paragraph) > 10 && !c.containsSensitiveWords(paragraph) {
			validParagraphs = append(validParagraphs, paragraph)
		}
	}

	return strings.Join(validParagraphs, "\n")
}



// removeSensitiveContent 移除敏感词相关内容
func (c *DefaultNewsCleaner) removeSensitiveContent(text string) string {
	for _, word := range c.sensitiveWords {
		if strings.Contains(text, word) {
			// 找到包含敏感词的句子并移除
			sentences := strings.Split(text, "。")
			validSentences := make([]string, 0, len(sentences))

			for _, sentence := range sentences {
				if !strings.Contains(sentence, word) {
					validSentences = append(validSentences, sentence)
				}
			}

			text = strings.Join(validSentences, "。")
		}
	}

	return text
}

// containsSensitiveWords 检查是否包含敏感词
func (c *DefaultNewsCleaner) containsSensitiveWords(text string) bool {
	for _, word := range c.sensitiveWords {
		if strings.Contains(text, word) {
			return true
		}
	}
	return false
}

// isValidCleanedNews 验证清洗后的新闻是否有效
func (c *DefaultNewsCleaner) isValidCleanedNews(news *models.News) bool {
	if news == nil {
		logger.Warnf("清洗验证失败: 新闻为nil")
		return false
	}

	// 检查标题长度
	if len(strings.TrimSpace(news.Title)) < 5 {
		logger.Warnf("清洗验证失败: 标题过短, 标题='%s', 长度=%d", news.Title, len(strings.TrimSpace(news.Title)))
		return false
	}

	// 检查内容长度
	if len(strings.TrimSpace(news.Content)) < 20 {
		logger.Warnf("清洗验证失败: 内容过短, 内容='%s', 长度=%d", news.Content, len(strings.TrimSpace(news.Content)))
		return false
	}

	// 检查是否包含有效的中文字符
	if !c.containsValidChineseContent(news.Title) && !c.containsValidChineseContent(news.Content) {
		logger.Warnf("清洗验证失败: 缺少有效中文内容, 标题='%s', 内容='%s'", news.Title, news.Content)
		return false
	}

	logger.Infof("清洗验证成功: 标题='%s', 内容长度=%d", news.Title, len(strings.TrimSpace(news.Content)))
	return true
}

// containsValidChineseContent 检查是否包含有效的中文内容
func (c *DefaultNewsCleaner) containsValidChineseContent(text string) bool {
	chineseCount := 0
	totalCount := 0

	for _, r := range text {
		if unicode.Is(unicode.Han, r) {
			chineseCount++
		}
		if !unicode.IsSpace(r) {
			totalCount++
		}
	}

	// 中文字符占比超过30%认为是有效的中文内容
	return totalCount > 0 && float64(chineseCount)/float64(totalCount) > 0.3
}

// GetCleanerInfo 获取清洗器信息
func (c *DefaultNewsCleaner) GetCleanerInfo() map[string]interface{} {
	return map[string]interface{}{
		"name":        "默认新闻数据清洗器",
		"description": "清洗新闻数据，移除HTML标签、特殊字符、敏感词等",
		"version":     "1.0.0",
		"features": []string{
			"HTML标签清理",
			"特殊字符过滤",
			"敏感词移除",
			"内容验证",
			"关键词去重",
			"标签规范化",
		},
		"sensitive_words_count": len(c.sensitiveWords),
	}
}