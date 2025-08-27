package handler

import (
	"context"
	"net/http"
	"strconv"
	"time"

	"data-collector/internal/models"
	"data-collector/internal/services"
	"data-collector/internal/storage"

	"github.com/gin-gonic/gin"
	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/bson/primitive"
)

// Response 通用响应结构
type Response struct {
	Code    int         `json:"code"`    // 响应码
	Message string      `json:"message"` // 响应消息
	Data    interface{} `json:"data,omitempty"` // 响应数据
	Error   string      `json:"error,omitempty"` // 错误信息
}

// NewsHandler 新闻API处理器
type NewsHandler struct {
	newsRepo    storage.NewsRepository
	newsService *services.NewsService
}

// NewNewsHandler 创建新闻处理器
func NewNewsHandler(newsRepo storage.NewsRepository, newsService *services.NewsService) *NewsHandler {
	return &NewsHandler{
		newsRepo:    newsRepo,
		newsService: newsService,
	}
}

// GetNewsList 获取新闻列表
// @Summary 获取新闻列表
// @Description 根据条件获取新闻列表，支持分页
// @Tags 新闻管理
// @Accept json
// @Produce json
// @Param limit query int false "每页数量" default(20)
// @Param offset query int false "偏移量" default(0)
// @Param source query string false "新闻来源"
// @Param keyword query string false "关键词搜索"
// @Param stock_code query string false "关联股票代码"
// @Success 200 {object} Response{data=NewsListResponse}
// @Failure 400 {object} Response
// @Failure 500 {object} Response
// @Router /api/v1/news [get]
func (h *NewsHandler) GetNewsList(c *gin.Context) {
	// 解析查询参数
	limit, _ := strconv.ParseInt(c.DefaultQuery("limit", "20"), 10, 64)
	offset, _ := strconv.ParseInt(c.DefaultQuery("offset", "0"), 10, 64)
	source := c.Query("source")
	keyword := c.Query("keyword")
	stockCode := c.Query("stock_code")

	// 参数验证
	if limit <= 0 || limit > 100 {
		limit = 20
	}
	if offset < 0 {
		offset = 0
	}

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	var newsList []*models.News
	var err error

	// 根据不同条件查询
	switch {
	case keyword != "":
		// 关键词搜索
		newsList, err = h.newsRepo.SearchByKeyword(ctx, keyword, limit, offset)
	case stockCode != "":
		// 按关联股票查询
		newsList, err = h.newsRepo.GetByRelatedStock(ctx, stockCode, limit, offset)
	default:
		// 普通列表查询
		filter := bson.M{}
		if source != "" {
			filter["source"] = source
		}
		newsList, err = h.newsRepo.GetList(ctx, filter, limit, offset)
	}

	if err != nil {
		c.JSON(http.StatusInternalServerError, Response{
			Code:    500,
			Message: "获取新闻列表失败",
			Error:   err.Error(),
		})
		return
	}

	// 获取总数
	filter := bson.M{}
	if source != "" {
		filter["source"] = source
	}
	total, err := h.newsRepo.Count(ctx, filter)
	if err != nil {
		total = 0 // 如果获取总数失败，设为0
	}

	c.JSON(http.StatusOK, Response{
		Code:    200,
		Message: "获取成功",
		Data: NewsListResponse{
			List:   newsList,
			Total:  total,
			Limit:  limit,
			Offset: offset,
		},
	})
}

// GetNewsByID 根据ID获取新闻详情
// @Summary 获取新闻详情
// @Description 根据新闻ID获取详细信息
// @Tags 新闻管理
// @Accept json
// @Produce json
// @Param id path string true "新闻ID"
// @Success 200 {object} Response{data=models.News}
// @Failure 400 {object} Response
// @Failure 404 {object} Response
// @Failure 500 {object} Response
// @Router /api/v1/news/detail [get]
func (h *NewsHandler) GetNewsByID(c *gin.Context) {
	idStr := c.Query("id")
	if idStr == "" {
		c.JSON(http.StatusBadRequest, Response{
			Code:    400,
			Message: "新闻ID不能为空",
		})
		return
	}

	// 解析ObjectID
	id, err := primitive.ObjectIDFromHex(idStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, Response{
			Code:    400,
			Message: "无效的新闻ID格式",
			Error:   err.Error(),
		})
		return
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	news, err := h.newsRepo.GetByID(ctx, id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, Response{
			Code:    500,
			Message: "获取新闻详情失败",
			Error:   err.Error(),
		})
		return
	}

	if news == nil {
		c.JSON(http.StatusNotFound, Response{
			Code:    404,
			Message: "新闻不存在",
		})
		return
	}

	c.JSON(http.StatusOK, Response{
		Code:    200,
		Message: "获取成功",
		Data:    news,
	})
}

// GetNewsByTimeRange 根据时间范围获取新闻
// @Summary 根据时间范围获取新闻
// @Description 获取指定时间范围内的新闻列表
// @Tags 新闻管理
// @Accept json
// @Produce json
// @Param start_time query string true "开始时间" format(date-time)
// @Param end_time query string true "结束时间" format(date-time)
// @Param limit query int false "每页数量" default(20)
// @Param offset query int false "偏移量" default(0)
// @Success 200 {object} Response{data=NewsListResponse}
// @Failure 400 {object} Response
// @Failure 500 {object} Response
// @Router /api/v1/news/time-range [get]
func (h *NewsHandler) GetNewsByTimeRange(c *gin.Context) {
	startTimeStr := c.Query("start_time")
	endTimeStr := c.Query("end_time")
	limit, _ := strconv.ParseInt(c.DefaultQuery("limit", "20"), 10, 64)
	offset, _ := strconv.ParseInt(c.DefaultQuery("offset", "0"), 10, 64)

	// 参数验证
	if startTimeStr == "" || endTimeStr == "" {
		c.JSON(http.StatusBadRequest, Response{
			Code:    400,
			Message: "开始时间和结束时间不能为空",
		})
		return
	}

	if limit <= 0 || limit > 100 {
		limit = 20
	}
	if offset < 0 {
		offset = 0
	}

	// 解析时间
	startTime, err := time.Parse(time.RFC3339, startTimeStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, Response{
			Code:    400,
			Message: "开始时间格式错误，请使用RFC3339格式",
			Error:   err.Error(),
		})
		return
	}

	endTime, err := time.Parse(time.RFC3339, endTimeStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, Response{
			Code:    400,
			Message: "结束时间格式错误，请使用RFC3339格式",
			Error:   err.Error(),
		})
		return
	}

	// 验证时间范围
	if startTime.After(endTime) {
		c.JSON(http.StatusBadRequest, Response{
			Code:    400,
			Message: "开始时间不能晚于结束时间",
		})
		return
	}

	// 限制查询范围（最多查询30天）
	if endTime.Sub(startTime) > 30*24*time.Hour {
		c.JSON(http.StatusBadRequest, Response{
			Code:    400,
			Message: "查询时间范围不能超过30天",
		})
		return
	}

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	newsList, err := h.newsRepo.GetByTimeRange(ctx, startTime, endTime, limit, offset)
	if err != nil {
		c.JSON(http.StatusInternalServerError, Response{
			Code:    500,
			Message: "获取新闻列表失败",
			Error:   err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, Response{
		Code:    200,
		Message: "获取成功",
		Data: NewsListResponse{
			List:   newsList,
			Total:  int64(len(newsList)), // 简化处理，实际应该查询总数
			Limit:  limit,
			Offset: offset,
		},
	})
}

// SearchNews 搜索新闻
// @Summary 搜索新闻
// @Description 根据关键词搜索新闻
// @Tags 新闻管理
// @Accept json
// @Produce json
// @Param keyword query string true "搜索关键词"
// @Param limit query int false "每页数量" default(20)
// @Param offset query int false "偏移量" default(0)
// @Success 200 {object} Response{data=NewsListResponse}
// @Failure 400 {object} Response
// @Failure 500 {object} Response
// @Router /api/v1/news/search [get]
func (h *NewsHandler) SearchNews(c *gin.Context) {
	keyword := c.Query("keyword")
	limit, _ := strconv.ParseInt(c.DefaultQuery("limit", "20"), 10, 64)
	offset, _ := strconv.ParseInt(c.DefaultQuery("offset", "0"), 10, 64)

	// 参数验证
	if keyword == "" {
		c.JSON(http.StatusBadRequest, Response{
			Code:    400,
			Message: "搜索关键词不能为空",
		})
		return
	}

	if limit <= 0 || limit > 100 {
		limit = 20
	}
	if offset < 0 {
		offset = 0
	}

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	newsList, err := h.newsRepo.SearchByKeyword(ctx, keyword, limit, offset)
	if err != nil {
		c.JSON(http.StatusInternalServerError, Response{
			Code:    500,
			Message: "搜索新闻失败",
			Error:   err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, Response{
		Code:    200,
		Message: "搜索成功",
		Data: NewsListResponse{
			List:   newsList,
			Total:  int64(len(newsList)), // 简化处理
			Limit:  limit,
			Offset: offset,
		},
	})
}

// GetNewsByStock 根据股票代码获取相关新闻
// @Summary 根据股票代码获取相关新闻
// @Description 获取与指定股票相关的新闻列表
// @Tags 新闻管理
// @Accept json
// @Produce json
// @Param stock_code path string true "股票代码"
// @Param limit query int false "每页数量" default(20)
// @Param offset query int false "偏移量" default(0)
// @Success 200 {object} Response{data=NewsListResponse}
// @Failure 400 {object} Response
// @Failure 500 {object} Response
// @Router /api/v1/news/by-stock [get]
func (h *NewsHandler) GetNewsByStock(c *gin.Context) {
	stockCode := c.Query("stock_code")
	limit, _ := strconv.ParseInt(c.DefaultQuery("limit", "20"), 10, 64)
	offset, _ := strconv.ParseInt(c.DefaultQuery("offset", "0"), 10, 64)

	// 参数验证
	if stockCode == "" {
		c.JSON(http.StatusBadRequest, Response{
			Code:    400,
			Message: "股票代码不能为空",
		})
		return
	}

	if limit <= 0 || limit > 100 {
		limit = 20
	}
	if offset < 0 {
		offset = 0
	}

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	newsList, err := h.newsRepo.GetByRelatedStock(ctx, stockCode, limit, offset)
	if err != nil {
		c.JSON(http.StatusInternalServerError, Response{
			Code:    500,
			Message: "获取股票相关新闻失败",
			Error:   err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, Response{
		Code:    200,
		Message: "获取成功",
		Data: NewsListResponse{
			List:   newsList,
			Total:  int64(len(newsList)), // 简化处理
			Limit:  limit,
			Offset: offset,
		},
	})
}

// TriggerCollection 手动触发新闻采集
// @Summary 手动触发新闻采集
// @Description 手动触发一次新闻采集任务
// @Tags 新闻管理
// @Accept json
// @Produce json
// @Success 200 {object} Response
// @Failure 500 {object} Response
// @Router /api/v1/news/collect [post]
func (h *NewsHandler) TriggerCollection(c *gin.Context) {
	if h.newsService == nil {
		c.JSON(http.StatusInternalServerError, Response{
			Code:    500,
			Message: "新闻服务未初始化",
		})
		return
	}

	err := h.newsService.TriggerCollection()
	if err != nil {
		c.JSON(http.StatusInternalServerError, Response{
			Code:    500,
			Message: "触发新闻采集失败",
			Error:   err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, Response{
		Code:    200,
		Message: "新闻采集任务已触发",
	})
}

// GetServiceStatus 获取新闻服务状态
// @Summary 获取新闻服务状态
// @Description 获取新闻服务运行状态和统计信息
// @Tags 新闻管理
// @Accept json
// @Produce json
// @Success 200 {object} Response
// @Failure 500 {object} Response
// @Router /api/v1/news/status [get]
func (h *NewsHandler) GetServiceStatus(c *gin.Context) {
	if h.newsService == nil {
		c.JSON(http.StatusInternalServerError, Response{
			Code:    500,
			Message: "新闻服务未初始化",
		})
		return
	}

	status := h.newsService.GetStatus()
	c.JSON(http.StatusOK, Response{
		Code:    200,
		Message: "获取成功",
		Data:    status,
	})
}

// NewsListResponse 新闻列表响应
type NewsListResponse struct {
	List   []*models.News `json:"list"`   // 新闻列表
	Total  int64         `json:"total"`  // 总数
	Limit  int64         `json:"limit"`  // 每页数量
	Offset int64         `json:"offset"` // 偏移量
}