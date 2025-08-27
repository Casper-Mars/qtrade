package storage

import (
	"context"
	"time"

	"data-collector/internal/models"
	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/bson/primitive"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

// PolicyRepository 政策数据存储接口
type PolicyRepository interface {
	// 创建政策
	Create(ctx context.Context, policy *models.Policy) error
	// 批量创建政策
	BatchCreate(ctx context.Context, policies []*models.Policy) error
	// 根据ID获取政策
	GetByID(ctx context.Context, id primitive.ObjectID) (*models.Policy, error)
	// 获取政策列表
	GetList(ctx context.Context, filter bson.M, limit, offset int64) ([]*models.Policy, error)
	// 根据时间范围获取政策
	GetByTimeRange(ctx context.Context, startTime, endTime time.Time, limit, offset int64) ([]*models.Policy, error)
	// 根据政策类型获取政策
	GetByPolicyType(ctx context.Context, policyType string, limit, offset int64) ([]*models.Policy, error)
	// 根据影响级别获取政策
	GetByImpactLevel(ctx context.Context, impactLevel string, limit, offset int64) ([]*models.Policy, error)
	// 根据关键词搜索政策
	SearchByKeyword(ctx context.Context, keyword string, limit, offset int64) ([]*models.Policy, error)
	// 根据发布机构获取政策
	GetBySource(ctx context.Context, source string, limit, offset int64) ([]*models.Policy, error)
	// 更新政策
	Update(ctx context.Context, id primitive.ObjectID, update bson.M) error
	// 删除政策
	Delete(ctx context.Context, id primitive.ObjectID) error
	// 检查政策是否存在（用于去重）
	Exists(ctx context.Context, title, source string, publishTime time.Time) (bool, error)
	// 获取总数
	Count(ctx context.Context, filter bson.M) (int64, error)
}

// policyRepository 政策数据存储实现
type policyRepository struct {
	collection *mongo.Collection
}

// NewPolicyRepository 创建政策数据存储实例
func NewPolicyRepository(db *mongo.Database) PolicyRepository {
	return &policyRepository{
		collection: db.Collection("policies"),
	}
}

// Create 创建政策
func (r *policyRepository) Create(ctx context.Context, policy *models.Policy) error {
	policy.CreatedAt = time.Now()
	policy.UpdatedAt = time.Now()
	
	_, err := r.collection.InsertOne(ctx, policy)
	return err
}

// BatchCreate 批量创建政策
func (r *policyRepository) BatchCreate(ctx context.Context, policies []*models.Policy) error {
	if len(policies) == 0 {
		return nil
	}
	
	docs := make([]interface{}, len(policies))
	for i, policy := range policies {
		policy.CreatedAt = time.Now()
		policy.UpdatedAt = time.Now()
		docs[i] = policy
	}
	
	_, err := r.collection.InsertMany(ctx, docs)
	return err
}

// GetByID 根据ID获取政策
func (r *policyRepository) GetByID(ctx context.Context, id primitive.ObjectID) (*models.Policy, error) {
	var policy models.Policy
	err := r.collection.FindOne(ctx, bson.M{"_id": id}).Decode(&policy)
	if err != nil {
		return nil, err
	}
	return &policy, nil
}

// GetList 获取政策列表
func (r *policyRepository) GetList(ctx context.Context, filter bson.M, limit, offset int64) ([]*models.Policy, error) {
	opts := options.Find()
	if limit > 0 {
		opts.SetLimit(limit)
	}
	if offset > 0 {
		opts.SetSkip(offset)
	}
	opts.SetSort(bson.D{{"publish_time", -1}}) // 按发布时间倒序
	
	cursor, err := r.collection.Find(ctx, filter, opts)
	if err != nil {
		return nil, err
	}
	defer cursor.Close(ctx)
	
	var policies []*models.Policy
	for cursor.Next(ctx) {
		var policy models.Policy
		if err := cursor.Decode(&policy); err != nil {
			return nil, err
		}
		policies = append(policies, &policy)
	}
	
	return policies, cursor.Err()
}

// GetByTimeRange 根据时间范围获取政策
func (r *policyRepository) GetByTimeRange(ctx context.Context, startTime, endTime time.Time, limit, offset int64) ([]*models.Policy, error) {
	filter := bson.M{
		"publish_time": bson.M{
			"$gte": startTime,
			"$lte": endTime,
		},
	}
	return r.GetList(ctx, filter, limit, offset)
}

// GetByPolicyType 根据政策类型获取政策
func (r *policyRepository) GetByPolicyType(ctx context.Context, policyType string, limit, offset int64) ([]*models.Policy, error) {
	filter := bson.M{"policy_type": policyType}
	return r.GetList(ctx, filter, limit, offset)
}

// GetByImpactLevel 根据影响级别获取政策
func (r *policyRepository) GetByImpactLevel(ctx context.Context, impactLevel string, limit, offset int64) ([]*models.Policy, error) {
	filter := bson.M{"impact_level": impactLevel}
	return r.GetList(ctx, filter, limit, offset)
}

// SearchByKeyword 根据关键词搜索政策
func (r *policyRepository) SearchByKeyword(ctx context.Context, keyword string, limit, offset int64) ([]*models.Policy, error) {
	filter := bson.M{
		"$or": []bson.M{
			{"title": bson.M{"$regex": keyword, "$options": "i"}},
			{"content": bson.M{"$regex": keyword, "$options": "i"}},
			{"keywords": bson.M{"$in": []string{keyword}}},
		},
	}
	return r.GetList(ctx, filter, limit, offset)
}

// GetBySource 根据发布机构获取政策
func (r *policyRepository) GetBySource(ctx context.Context, source string, limit, offset int64) ([]*models.Policy, error) {
	filter := bson.M{"source": source}
	return r.GetList(ctx, filter, limit, offset)
}

// Update 更新政策
func (r *policyRepository) Update(ctx context.Context, id primitive.ObjectID, update bson.M) error {
	update["updated_at"] = time.Now()
	_, err := r.collection.UpdateOne(ctx, bson.M{"_id": id}, bson.M{"$set": update})
	return err
}

// Delete 删除政策
func (r *policyRepository) Delete(ctx context.Context, id primitive.ObjectID) error {
	_, err := r.collection.DeleteOne(ctx, bson.M{"_id": id})
	return err
}

// Exists 检查政策是否存在（用于去重）
func (r *policyRepository) Exists(ctx context.Context, title, source string, publishTime time.Time) (bool, error) {
	// 使用标题、来源和发布时间的组合来判断是否重复
	filter := bson.M{
		"title":        title,
		"source":       source,
		"publish_time": publishTime,
	}
	
	count, err := r.collection.CountDocuments(ctx, filter)
	if err != nil {
		return false, err
	}
	
	return count > 0, nil
}

// Count 获取总数
func (r *policyRepository) Count(ctx context.Context, filter bson.M) (int64, error) {
	return r.collection.CountDocuments(ctx, filter)
}