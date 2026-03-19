import { Skeleton, Card, List } from 'antd';

/**
 * 新闻列表 Skeleton 加载组件
 */
export const NewsListSkeleton = ({ count = 10 }) => {
  return (
    <List
      grid={{ gutter: 16, column: 3 }}
      dataSource={Array(count)}
      renderItem={() => (
        <List.Item>
          <Card>
            <Skeleton avatar paragraph={{ rows: 3 }} active />
          </Card>
        </List.Item>
      )}
    />
  );
};

/**
 * 卡片列表 Skeleton
 */
export const CardListSkeleton = ({ count = 6 }) => {
  return (
    <List
      grid={{ gutter: 16, column: 3 }}
      dataSource={Array(count)}
      renderItem={() => (
        <List.Item>
          <Card
            cover={
              <Skeleton.Image active style={{ height: 160 }} />
            }
          >
            <Skeleton active paragraph={{ rows: 2 }} title={false} />
          </Card>
        </List.Item>
      )}
    />
  );
};

/**
 * 详情页面 Skeleton
 */
export const DetailSkeleton = () => {
  return (
    <div style={{ padding: 24 }}>
      <Skeleton paragraph={{ rows: 2 }} active style={{ marginBottom: 24 }} />
      <Skeleton avatar paragraph={{ rows: 6 }} active />
    </div>
  );
};

/**
 * 统计卡片 Skeleton
 */
export const StatsSkeleton = () => {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
      {Array(4).fill(0).map((_, i) => (
        <Card key={i}>
          <Skeleton active paragraph={{ rows: 1 }} title={false} />
        </Card>
      ))}
    </div>
  );
};

export default {
  NewsListSkeleton,
  CardListSkeleton,
  DetailSkeleton,
  StatsSkeleton,
};
