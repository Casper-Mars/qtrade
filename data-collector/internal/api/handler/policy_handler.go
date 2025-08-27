package handler

import (
	"context"
	"net/http"
	"strconv"
	"time"

	"data-collector/internal/models"
	"data-collector/internal/storage"

	"github.com/gin-gonic/gin"
	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/bson/primitive"
)

// PolicyHandler 政策API处理器
type PolicyHandler struct {
	policyRepo storage.PolicyRepository
}

// PolicyListResponse 政策列表响应
type PolicyListResponse struct {
	Policies []models.Policy `json:"policies"`
	Total    int64           `json:"total"`
	Limit    int64           `json:"limit"`
	Offset   int64           `json:"offset"`
}

// NewPolicyHandler 创建政策处理器
func NewPolicyHandler(policyRepo storage.PolicyRepository) *PolicyHandler {
	return &PolicyHandler{
		policyRepo: policyRepo,
	}
}

// GetPolicyList 获取政策列表
// @Summary 获取政策列表
// @Description 根据条件获取政策列表，支持分页
// @Tags 政策管理
// @Accept json
// @Produce json
// @Param limit query int false "每页数量" default(20)
// @Param offset query int false "偏移量" default(0)
// @Param source query string false "发布机构"
// @Param policy_type query string false "政策类型"
// @Param impact_level query string false "影响级别"
// @Success 200 {object} Response{data=PolicyListResponse}
// @Failure 400 {object} Response
// @Failure 500 {object} Response
// @Router /api/v1/policies [get]
func (h *PolicyHandler) GetPolicyList(c *gin.Context) {
	// 解析查询参数
	limit, _ := strconv.ParseInt(c.DefaultQuery("limit", "20"), 10, 64)
	offset, _ := strconv.ParseInt(c.DefaultQuery("offset", "0"), 10, 64)
	source := c.Query("source")
	policyType := c.Query("policy_type")
	impactLevel := c.Query("impact_level")

	// 参数验证
	if limit <= 0 || limit > 100 {
		limit = 20
	}
	if offset < 0 {
		offset = 0
	}

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	var policies []*models.Policy
	var err error

	// 根据不同条件查询
	switch {
	case source != "":
		// 按发布机构查询
		policies, err = h.policyRepo.GetBySource(ctx, source, limit, offset)
	case policyType != "":
		// 按政策类型查询
		policies, err = h.policyRepo.GetByPolicyType(ctx, policyType, limit, offset)
	case impactLevel != "":
		// 按影响级别查询
		policies, err = h.policyRepo.GetByImpactLevel(ctx, impactLevel, limit, offset)
	default:
		// 普通列表查询
		filter := bson.M{}
		policies, err = h.policyRepo.GetList(ctx, filter, limit, offset)
	}

	if err != nil {
		c.JSON(http.StatusInternalServerError, Response{
			Code:    500,
			Message: "获取政策列表失败",
			Error:   err.Error(),
		})
		return
	}

	// 获取总数
	filter := bson.M{}
	if source != "" {
		filter["source"] = source
	}
	if policyType != "" {
		filter["policy_type"] = policyType
	}
	if impactLevel != "" {
		filter["impact_level"] = impactLevel
	}

	total, err := h.policyRepo.Count(ctx, filter)
	if err != nil {
		c.JSON(http.StatusInternalServerError, Response{
			Code:    500,
			Message: "获取政策总数失败",
			Error:   err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, Response{
		Code:    200,
		Message: "获取政策列表成功",
		Data: gin.H{
			"policies": policies,
			"total":    total,
			"limit":    limit,
			"offset":   offset,
		},
	})
}

// GetPolicyByID 根据ID获取政策详情
// @Summary 根据ID获取政策详情
// @Description 根据政策ID获取政策详细信息
// @Tags 政策管理
// @Accept json
// @Produce json
// @Param id path string true "政策ID"
// @Success 200 {object} Response{data=models.Policy}
// @Failure 400 {object} Response
// @Failure 404 {object} Response
// @Failure 500 {object} Response
// @Router /api/v1/policies/{id} [get]
func (h *PolicyHandler) GetPolicyByID(c *gin.Context) {
	idStr := c.Query("id")
	if idStr == "" {
		c.JSON(http.StatusBadRequest, Response{
			Code:    400,
			Message: "政策ID不能为空",
		})
		return
	}

	// 转换ObjectID
	id, err := primitive.ObjectIDFromHex(idStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, Response{
			Code:    400,
			Message: "无效的政策ID格式",
			Error:   err.Error(),
		})
		return
	}

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	policy, err := h.policyRepo.GetByID(ctx, id)
	if err != nil {
		if err.Error() == "mongo: no documents in result" {
			c.JSON(http.StatusNotFound, Response{
				Code:    404,
				Message: "政策不存在",
			})
			return
		}
		c.JSON(http.StatusInternalServerError, Response{
			Code:    500,
			Message: "获取政策详情失败",
			Error:   err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, Response{
		Code:    200,
		Message: "获取政策详情成功",
		Data:    policy,
	})
}

// GetPoliciesByTimeRange 根据时间范围获取政策
// @Summary 根据时间范围获取政策
// @Description 根据发布时间范围获取政策列表
// @Tags 政策管理
// @Accept json
// @Produce json
// @Param start_time query string true "开始时间" format(date-time)
// @Param end_time query string true "结束时间" format(date-time)
// @Param limit query int false "每页数量" default(20)
// @Param offset query int false "偏移量" default(0)
// @Success 200 {object} Response{data=PolicyListResponse}
// @Failure 400 {object} Response
// @Failure 500 {object} Response
// @Router /api/v1/policies/time-range [get]
func (h *PolicyHandler) GetPoliciesByTimeRange(c *gin.Context) {
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

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	policies, err := h.policyRepo.GetByTimeRange(ctx, startTime, endTime, limit, offset)
	if err != nil {
		c.JSON(http.StatusInternalServerError, Response{
			Code:    500,
			Message: "获取政策列表失败",
			Error:   err.Error(),
		})
		return
	}

	// 获取总数
	filter := bson.M{
		"publish_time": bson.M{
			"$gte": startTime,
			"$lte": endTime,
		},
	}
	total, err := h.policyRepo.Count(ctx, filter)
	if err != nil {
		c.JSON(http.StatusInternalServerError, Response{
			Code:    500,
			Message: "获取政策总数失败",
			Error:   err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, Response{
		Code:    200,
		Message: "获取政策列表成功",
		Data: gin.H{
			"policies":   policies,
			"total":      total,
			"limit":      limit,
			"offset":     offset,
			"start_time": startTime,
			"end_time":   endTime,
		},
	})
}

// SearchPolicies 搜索政策
// @Summary 搜索政策
// @Description 根据关键词搜索政策
// @Tags 政策管理
// @Accept json
// @Produce json
// @Param keyword query string true "搜索关键词"
// @Param limit query int false "每页数量" default(20)
// @Param offset query int false "偏移量" default(0)
// @Success 200 {object} Response{data=PolicyListResponse}
// @Failure 400 {object} Response
// @Failure 500 {object} Response
// @Router /api/v1/policies/search [get]
func (h *PolicyHandler) SearchPolicies(c *gin.Context) {
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

	policies, err := h.policyRepo.SearchByKeyword(ctx, keyword, limit, offset)
	if err != nil {
		c.JSON(http.StatusInternalServerError, Response{
			Code:    500,
			Message: "搜索政策失败",
			Error:   err.Error(),
		})
		return
	}

	// 获取搜索结果总数
	filter := bson.M{
		"$or": []bson.M{
			{"title": bson.M{"$regex": keyword, "$options": "i"}},
			{"content": bson.M{"$regex": keyword, "$options": "i"}},
			{"keywords": bson.M{"$in": []string{keyword}}},
		},
	}
	total, err := h.policyRepo.Count(ctx, filter)
	if err != nil {
		c.JSON(http.StatusInternalServerError, Response{
			Code:    500,
			Message: "获取搜索结果总数失败",
			Error:   err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, Response{
		Code:    200,
		Message: "搜索政策成功",
		Data: gin.H{
			"policies": policies,
			"total":    total,
			"limit":    limit,
			"offset":   offset,
			"keyword":  keyword,
		},
	})
}

// GetPoliciesByType 根据政策类型获取政策
// @Summary 根据政策类型获取政策
// @Description 根据政策类型获取政策列表
// @Tags 政策管理
// @Accept json
// @Produce json
// @Param policy_type path string true "政策类型"
// @Param limit query int false "每页数量" default(20)
// @Param offset query int false "偏移量" default(0)
// @Success 200 {object} Response{data=PolicyListResponse}
// @Failure 400 {object} Response
// @Failure 500 {object} Response
// @Router /api/v1/policies/type/{policy_type} [get]
func (h *PolicyHandler) GetPoliciesByType(c *gin.Context) {
	policyType := c.Query("policy_type")
	limit, _ := strconv.ParseInt(c.DefaultQuery("limit", "20"), 10, 64)
	offset, _ := strconv.ParseInt(c.DefaultQuery("offset", "0"), 10, 64)

	// 参数验证
	if policyType == "" {
		c.JSON(http.StatusBadRequest, Response{
			Code:    400,
			Message: "政策类型不能为空",
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

	policies, err := h.policyRepo.GetByPolicyType(ctx, policyType, limit, offset)
	if err != nil {
		c.JSON(http.StatusInternalServerError, Response{
			Code:    500,
			Message: "获取政策列表失败",
			Error:   err.Error(),
		})
		return
	}

	// 获取总数
	filter := bson.M{"policy_type": policyType}
	total, err := h.policyRepo.Count(ctx, filter)
	if err != nil {
		c.JSON(http.StatusInternalServerError, Response{
			Code:    500,
			Message: "获取政策总数失败",
			Error:   err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, Response{
		Code:    200,
		Message: "获取政策列表成功",
		Data: gin.H{
			"policies":    policies,
			"total":       total,
			"limit":       limit,
			"offset":      offset,
			"policy_type": policyType,
		},
	})
}