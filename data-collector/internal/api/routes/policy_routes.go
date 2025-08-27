package routes

import (
	"data-collector/internal/api/handler"
	"data-collector/internal/storage"

	"github.com/gin-gonic/gin"
)

// SetupPolicyRoutes 设置政策相关路由
func SetupPolicyRoutes(router *gin.RouterGroup, policyRepo storage.PolicyRepository) {
	// 创建政策处理器
	policyHandler := handler.NewPolicyHandler(policyRepo)

	// 政策管理路由组
	policyGroup := router.Group("/policies")
	{
		// 获取政策列表
		policyGroup.GET("", policyHandler.GetPolicyList)
		
		// 根据ID获取政策详情 (使用查询参数: ?id=xxx)
		policyGroup.GET("/detail", policyHandler.GetPolicyByID)
		
		// 根据时间范围获取政策
		policyGroup.GET("/time-range", policyHandler.GetPoliciesByTimeRange)
		
		// 搜索政策
		policyGroup.GET("/search", policyHandler.SearchPolicies)
		
		// 根据政策类型获取政策 (使用查询参数: ?policy_type=xxx)
		policyGroup.GET("/by-type", policyHandler.GetPoliciesByType)
	}
}