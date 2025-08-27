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

// NewsRepository 新闻数据存储接口
type NewsRepository interface {
	// 创建新闻
	Create(ctx context.Context, news *models.News) error
	// 批量创建新闻
	BatchCreate(ctx context.Context, newsList []*models.News) error
	// 根据ID获取新闻
	GetByID(ctx context.Context, id primitive.ObjectID) (*models.News, error)
	// 获取新闻列表
	GetList(ctx context.Context, filter bson.M, limit, offset int64) ([]*models.News, error)
	// 根据时间范围获取新闻
	GetByTimeRange(ctx context.Context, startTime, endTime time.Time, limit, offset int64) ([]*models.News, error)
	// 根据关键词搜索新闻
	SearchByKeyword(ctx context.Context, keyword string, limit, offset int64) ([]*models.News, error)
	// 根据关联股票获取新闻
	GetByRelatedStock(ctx context.Context, stockCode string, limit, offset int64) ([]*models.News, error)
	// 更新新闻
	Update(ctx context.Context, id primitive.ObjectID, update bson.M) error
	// 删除新闻
	Delete(ctx context.Context, id primitive.ObjectID) error
	// 检查新闻是否存在（用于去重）
	Exists(ctx context.Context, title, content string) (bool, error)
	// 获取总数
	Count(ctx context.Context, filter bson.M) (int64, error)
}

// newsRepository 新闻数据存储实现
type newsRepository struct {
	collection *mongo.Collection
}

// NewNewsRepository 创建新闻数据存储实例
func NewNewsRepository(db *mongo.Database) NewsRepository {
	return &newsRepository{
		collection: db.Collection("news"),
	}
}

// Create 创建新闻
func (r *newsRepository) Create(ctx context.Context, news *models.News) error {
	news.CreatedAt = time.Now()
	news.UpdatedAt = time.Now()
	
	_, err := r.collection.InsertOne(ctx, news)
	return err
}

// BatchCreate 批量创建新闻
func (r *newsRepository) BatchCreate(ctx context.Context, newsList []*models.News) error {
	if len(newsList) == 0 {
		return nil
	}
	
	docs := make([]interface{}, len(newsList))
	for i, news := range newsList {
		news.CreatedAt = time.Now()
		news.UpdatedAt = time.Now()
		docs[i] = news
	}
	
	_, err := r.collection.InsertMany(ctx, docs)
	return err
}

// GetByID 根据ID获取新闻
func (r *newsRepository) GetByID(ctx context.Context, id primitive.ObjectID) (*models.News, error) {
	var news models.News
	err := r.collection.FindOne(ctx, bson.M{"_id": id}).Decode(&news)
	if err != nil {
		return nil, err
	}
	return &news, nil
}

// GetList 获取新闻列表
func (r *newsRepository) GetList(ctx context.Context, filter bson.M, limit, offset int64) ([]*models.News, error) {
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
	
	var newsList []*models.News
	for cursor.Next(ctx) {
		var news models.News
		if err := cursor.Decode(&news); err != nil {
			return nil, err
		}
		newsList = append(newsList, &news)
	}
	
	return newsList, cursor.Err()
}

// GetByTimeRange 根据时间范围获取新闻
func (r *newsRepository) GetByTimeRange(ctx context.Context, startTime, endTime time.Time, limit, offset int64) ([]*models.News, error) {
	filter := bson.M{
		"publish_time": bson.M{
			"$gte": startTime,
			"$lte": endTime,
		},
	}
	return r.GetList(ctx, filter, limit, offset)
}

// SearchByKeyword 根据关键词搜索新闻
func (r *newsRepository) SearchByKeyword(ctx context.Context, keyword string, limit, offset int64) ([]*models.News, error) {
	filter := bson.M{
		"$or": []bson.M{
			{"title": bson.M{"$regex": keyword, "$options": "i"}},
			{"content": bson.M{"$regex": keyword, "$options": "i"}},
		},
	}
	return r.GetList(ctx, filter, limit, offset)
}

// GetByRelatedStock 根据关联股票获取新闻
func (r *newsRepository) GetByRelatedStock(ctx context.Context, stockCode string, limit, offset int64) ([]*models.News, error) {
	filter := bson.M{
		"related_stocks.code": stockCode,
	}
	return r.GetList(ctx, filter, limit, offset)
}

// Update 更新新闻
func (r *newsRepository) Update(ctx context.Context, id primitive.ObjectID, update bson.M) error {
	update["updated_at"] = time.Now()
	_, err := r.collection.UpdateOne(ctx, bson.M{"_id": id}, bson.M{"$set": update})
	return err
}

// Delete 删除新闻
func (r *newsRepository) Delete(ctx context.Context, id primitive.ObjectID) error {
	_, err := r.collection.DeleteOne(ctx, bson.M{"_id": id})
	return err
}

// Exists 检查新闻是否存在（用于去重）
func (r *newsRepository) Exists(ctx context.Context, title, content string) (bool, error) {
	filter := bson.M{
		"$or": []bson.M{
			{"title": title},
			{"content": content},
		},
	}
	
	count, err := r.collection.CountDocuments(ctx, filter)
	if err != nil {
		return false, err
	}
	
	return count > 0, nil
}

// Count 获取总数
func (r *newsRepository) Count(ctx context.Context, filter bson.M) (int64, error) {
	return r.collection.CountDocuments(ctx, filter)
}