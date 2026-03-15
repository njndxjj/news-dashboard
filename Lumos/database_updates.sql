-- 扩展 Articles 表
ALTER TABLE Articles
ADD COLUMN category TEXT NOT NULL DEFAULT '';

ALTER TABLE Articles
ADD COLUMN views INTEGER NOT NULL DEFAULT 0;

-- 增加索引
CREATE INDEX idx_unique_id ON Users (unique_id);
CREATE INDEX idx_category ON Articles (category);

-- 建立兴趣点与文章的多对多关联表
CREATE TABLE InterestArticle (
    interest_id INTEGER,
    article_id INTEGER,
    FOREIGN KEY(interest_id) REFERENCES InterestPoints(id),
    FOREIGN KEY(article_id) REFERENCES Articles(id)
);

-- 示例数据初始化
INSERT INTO Users (username, email, subscribed_keywords, unique_id) VALUES
('Alice', 'alice@example.com', 'AI,Digital', 'uuid-alice'),
('Bob', 'bob@example.com', 'Supply Chain,Optimization', 'uuid-bob');

INSERT INTO Articles (title, link, keywords, category, views) VALUES
('AI在制造业中的应用', 'https://example.com/ai', 'AI,制造业', 'Technology', 102),
('供应链优化趋势', 'https://example.com/supply', 'Supply Chain,Optimization', 'Business', 65);

-- 数据完整性校验（SQLite 不支持在 ALTER TABLE 中添加约束，跳过）