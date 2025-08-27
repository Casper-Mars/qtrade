package models

import (
	"time"

	"go.mongodb.org/mongo-driver/bson/primitive"
)

// News 新闻数据模型
type News struct {
	ID             primitive.ObjectID `bson:"_id,omitempty" json:"id"`
	Title          string             `bson:"title" json:"title"`                     // 快讯标题
	Content        string             `bson:"content" json:"content"`                 // 快讯内容
	Source         string             `bson:"source" json:"source"`                   // 来源（如：财联社）
	PublishTime    time.Time          `bson:"publish_time" json:"publish_time"`       // 发布时间
	URL            string             `bson:"url" json:"url"`                         // 原文链接
	RelatedStocks  []RelatedStock     `bson:"related_stocks" json:"related_stocks"`   // 关联股票
	RelatedIndustries []string        `bson:"related_industries" json:"related_industries"` // 关联行业
	CreatedAt      time.Time          `bson:"created_at" json:"created_at"`           // 创建时间
	UpdatedAt      time.Time          `bson:"updated_at" json:"updated_at"`           // 更新时间
}

// RelatedStock 关联股票信息
type RelatedStock struct {
	Code string `bson:"code" json:"code"` // 股票代码
	Name string `bson:"name" json:"name"` // 股票名称
}

// TableName 返回MongoDB集合名称
func (News) TableName() string {
	return "news"
}

// Policy 政策数据模型
type Policy struct {
	ID            primitive.ObjectID `bson:"_id,omitempty" json:"id"`
	Title         string             `bson:"title" json:"title"`                   // 政策标题
	Content       string             `bson:"content" json:"content"`               // 政策内容
	Source        string             `bson:"source" json:"source"`                 // 发布机构
	PolicyType    string             `bson:"policy_type" json:"policy_type"`       // 政策类型：货币政策|监管政策|交易规则
	PublishTime   time.Time          `bson:"publish_time" json:"publish_time"`     // 发布时间
	EffectiveTime *time.Time         `bson:"effective_time" json:"effective_time"` // 生效时间（可选）
	URL           string             `bson:"url" json:"url"`                       // 原文链接
	Keywords      []string           `bson:"keywords" json:"keywords"`             // 关键词
	ImpactLevel   string             `bson:"impact_level" json:"impact_level"`     // 影响级别：high|medium|low
	CreatedAt     time.Time          `bson:"created_at" json:"created_at"`         // 创建时间
	UpdatedAt     time.Time          `bson:"updated_at" json:"updated_at"`         // 更新时间
}

// TableName 返回MongoDB集合名称
func (Policy) TableName() string {
	return "policies"
}