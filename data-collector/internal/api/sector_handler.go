package api

import (
	"net/http"
	"strconv"
	"time"

	"data-collector/internal/collectors/market"
	"data-collector/internal/models"
	"data-collector/internal/storage"
	"data-collector/pkg/logger"

	"github.com/gin-gonic/gin"
)

// APIResponse 通用API响应
type APIResponse struct {
	Success bool        `json:"success"`
	Message string      `json:"message"`
	Data    interface{} `json:"data,omitempty"`
	Error   string      `json:"error,omitempty"`
}

// SectorHandler 板块分类API处理器
type SectorHandler struct {
	sectorCollector *market.SectorCollector
	sectorValidator *market.SectorValidator
	marketRepo      storage.MarketRepository
}

// NewSectorHandler 创建板块分类API处理器
func NewSectorHandler(sectorCollector *market.SectorCollector, sectorValidator *market.SectorValidator, marketRepo storage.MarketRepository) *SectorHandler {
	return &SectorHandler{
		sectorCollector: sectorCollector,
		sectorValidator: sectorValidator,
		marketRepo:      marketRepo,
	}
}

// CollectSectorClassificationRequest 采集板块分类请求
type CollectSectorClassificationRequest struct {
	ForceUpdate bool `json:"force_update"` // 是否强制更新
}

// CollectSectorConstituentsRequest 采集板块成分股请求
type CollectSectorConstituentsRequest struct {
	SectorCode string `json:"sector_code" binding:"required"` // 板块代码
}

// SectorListRequest 板块列表查询请求
type SectorListRequest struct {
	SectorType string `form:"sector_type"` // 板块类型
	Level      int    `form:"level"`       // 板块层级
	ParentCode string `form:"parent_code"` // 父级板块代码
	Limit      int    `form:"limit"`       // 限制数量
	Offset     int    `form:"offset"`      // 偏移量
}

// SectorConstituentsRequest 板块成分股查询请求
type SectorConstituentsRequest struct {
	SectorCode string `form:"sector_code" binding:"required"` // 板块代码
	Limit      int    `form:"limit"`                          // 限制数量
	Offset     int    `form:"offset"`                         // 偏移量
}

// CollectSectorClassification 采集板块分类信息
func (h *SectorHandler) CollectSectorClassification(c *gin.Context) {
	var req CollectSectorClassificationRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, APIResponse{
			Success: false,
			Message: "请求参数错误",
			Error:   err.Error(),
		})
		return
	}

	ctx := c.Request.Context()

	// 执行采集
	err := h.sectorCollector.CollectSectorClassification(ctx)
	if err != nil {
		logger.Error("采集板块分类信息失败", "error", err)
		c.JSON(http.StatusInternalServerError, APIResponse{
			Success: false,
			Message: "采集板块分类信息失败",
			Error:   err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, APIResponse{
		Success: true,
		Message: "板块分类信息采集成功",
		Data:    nil,
	})
}

// CollectSectorConstituents 采集板块成分股信息
func (h *SectorHandler) CollectSectorConstituents(c *gin.Context) {
	var req CollectSectorConstituentsRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, APIResponse{
			Success: false,
			Message: "请求参数错误",
			Error:   err.Error(),
		})
		return
	}

	ctx := c.Request.Context()

	// 执行采集
	err := h.sectorCollector.CollectSectorConstituents(ctx, req.SectorCode)
	if err != nil {
		logger.Error("采集板块成分股信息失败", "error", err, "sector_code", req.SectorCode)
		c.JSON(http.StatusInternalServerError, APIResponse{
			Success: false,
			Message: "采集板块成分股信息失败",
			Error:   err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, APIResponse{
		Success: true,
		Message: "板块成分股信息采集成功",
		Data:    nil,
	})
}

// CollectAllSectors 全板块批量采集
func (h *SectorHandler) CollectAllSectors(c *gin.Context) {
	ctx := c.Request.Context()

	// 执行全板块采集
	err := h.sectorCollector.CollectAllSectors(ctx)
	if err != nil {
		logger.Error("全板块批量采集失败", "error", err)
		c.JSON(http.StatusInternalServerError, APIResponse{
			Success: false,
			Message: "全板块批量采集失败",
			Error:   err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, APIResponse{
		Success: true,
		Message: "全板块批量采集成功",
		Data:    nil,
	})
}

// CollectIncrementalSectors 增量更新板块数据
func (h *SectorHandler) CollectIncrementalSectors(c *gin.Context) {
	sinceStr := c.Query("since")
	if sinceStr == "" {
		// 默认从7天前开始增量更新
		sinceStr = time.Now().AddDate(0, 0, -7).Format("2006-01-02")
	}

	since, err := time.Parse("2006-01-02", sinceStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, APIResponse{
			Success: false,
			Message: "日期格式错误，应为YYYY-MM-DD",
			Error:   err.Error(),
		})
		return
	}

	ctx := c.Request.Context()

	// 执行增量更新
	err = h.sectorCollector.CollectIncremental(ctx, since)
	if err != nil {
		logger.Error("增量更新板块数据失败", "error", err, "since", since)
		c.JSON(http.StatusInternalServerError, APIResponse{
			Success: false,
			Message: "增量更新板块数据失败",
			Error:   err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, APIResponse{
		Success: true,
		Message: "增量更新板块数据成功",
		Data:    nil,
	})
}

// GetSectorList 获取板块分类列表
func (h *SectorHandler) GetSectorList(c *gin.Context) {
	var req SectorListRequest
	if err := c.ShouldBindQuery(&req); err != nil {
		c.JSON(http.StatusBadRequest, APIResponse{
			Success: false,
			Message: "请求参数错误",
			Error:   err.Error(),
		})
		return
	}

	// 设置默认值
	if req.Limit <= 0 {
		req.Limit = 100
	}
	if req.Limit > 1000 {
		req.Limit = 1000
	}
	if req.Offset < 0 {
		req.Offset = 0
	}

	ctx := c.Request.Context()

	// 获取板块列表
	sectors, err := h.marketRepo.ListSectors(ctx, req.Limit, req.Offset)
	if err != nil {
		logger.Error("获取板块列表失败", "error", err)
		c.JSON(http.StatusInternalServerError, APIResponse{
			Success: false,
			Message: "获取板块列表失败",
			Error:   err.Error(),
		})
		return
	}

	// 根据查询条件过滤
	filteredSectors := h.filterSectors(sectors, req)

	c.JSON(http.StatusOK, APIResponse{
		Success: true,
		Message: "获取板块列表成功",
		Data: map[string]interface{}{
			"sectors": filteredSectors,
			"total":   len(filteredSectors),
			"limit":   req.Limit,
			"offset":  req.Offset,
		},
	})
}

// GetSectorConstituents 获取板块成分股
func (h *SectorHandler) GetSectorConstituents(c *gin.Context) {
	sectorCode := c.Query("sector_code")
	if sectorCode == "" {
		c.JSON(http.StatusBadRequest, APIResponse{
			Success: false,
			Message: "板块代码不能为空",
			Error:   "sector_code is required",
		})
		return
	}

	limitStr := c.Query("limit")
	offsetStr := c.Query("offset")

	limit := 100
	offset := 0

	if limitStr != "" {
		if l, err := strconv.Atoi(limitStr); err == nil && l > 0 {
			limit = l
		}
	}
	if limit > 1000 {
		limit = 1000
	}

	if offsetStr != "" {
		if o, err := strconv.Atoi(offsetStr); err == nil && o >= 0 {
			offset = o
		}
	}

	ctx := c.Request.Context()

	// 获取板块成分股
	constituents, err := h.marketRepo.GetSectorConstituents(ctx, sectorCode)
	if err != nil {
		logger.Error("获取板块成分股失败", "error", err, "sector_code", sectorCode)
		c.JSON(http.StatusInternalServerError, APIResponse{
			Success: false,
			Message: "获取板块成分股失败",
			Error:   err.Error(),
		})
		return
	}

	// 分页处理
	total := len(constituents)
	start := offset
	end := offset + limit
	if start > total {
		start = total
	}
	if end > total {
		end = total
	}

	pagedConstituents := constituents[start:end]

	c.JSON(http.StatusOK, APIResponse{
		Success: true,
		Message: "获取板块成分股成功",
		Data: map[string]interface{}{
			"sector_code":  sectorCode,
			"constituents": pagedConstituents,
			"total":        total,
			"limit":        limit,
			"offset":       offset,
		},
	})
}

// GetCollectorInfo 获取采集器信息
func (h *SectorHandler) GetCollectorInfo(c *gin.Context) {
	info := h.sectorCollector.GetCollectorInfo()
	c.JSON(http.StatusOK, APIResponse{
		Success: true,
		Message: "获取采集器信息成功",
		Data:    info,
	})
}

// GetValidatorInfo 获取验证器信息
func (h *SectorHandler) GetValidatorInfo(c *gin.Context) {
	info := h.sectorValidator.GetValidatorInfo()
	c.JSON(http.StatusOK, APIResponse{
		Success: true,
		Message: "获取验证器信息成功",
		Data:    info,
	})
}

// HealthCheck 健康检查
func (h *SectorHandler) HealthCheck(c *gin.Context) {
	c.JSON(http.StatusOK, APIResponse{
		Success: true,
		Message: "板块分类服务运行正常",
		Data: map[string]interface{}{
			"service":   "sector",
			"status":    "healthy",
			"timestamp": time.Now().Unix(),
		},
	})
}

// RegisterRoutes 注册路由
func (h *SectorHandler) RegisterRoutes(router *gin.RouterGroup) {
	sectorGroup := router.Group("/sectors")
	{
		// 数据采集接口
		sectorGroup.POST("/collect/classification", h.CollectSectorClassification)
		sectorGroup.POST("/collect/constituents", h.CollectSectorConstituents)
		sectorGroup.POST("/collect/all", h.CollectAllSectors)
		sectorGroup.POST("/collect/incremental", h.CollectIncrementalSectors)

		// 数据查询接口
		sectorGroup.GET("/list", h.GetSectorList)
		sectorGroup.GET("/constituents", h.GetSectorConstituents)

		// 系统信息接口
		sectorGroup.GET("/collector/info", h.GetCollectorInfo)
		sectorGroup.GET("/validator/info", h.GetValidatorInfo)
		sectorGroup.GET("/health", h.HealthCheck)
	}
}

// filterSectors 根据查询条件过滤板块
func (h *SectorHandler) filterSectors(sectors []*models.Sector, req SectorListRequest) []*models.Sector {
	var filtered []*models.Sector

	for _, sector := range sectors {
		// 按板块类型过滤
		if req.SectorType != "" && sector.SectorType != req.SectorType {
			continue
		}

		// 按板块层级过滤
		if req.Level > 0 && sector.Level != req.Level {
			continue
		}

		// 按父级板块代码过滤
		if req.ParentCode != "" && sector.ParentCode != req.ParentCode {
			continue
		}

		filtered = append(filtered, sector)
	}

	return filtered
}