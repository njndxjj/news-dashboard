import React, { useState, useEffect, useRef } from 'react';
import ReactDOM from 'react-dom/client';
import { apiRequest } from './services/api.js';
import { useToast } from './hooks/useToast.js';
import './App.css';
import './index.css';

// 兴趣图谱可视化组件
function InterestGraph() {
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [stats, setStats] = useState(null);
  const cyContainerRef = useRef(null);

  const { success, error: errorToast, ToastContainer } = useToast();

  // 获取兴趣图谱数据
  const fetchGraphData = async () => {
    setLoading(true);
    setError(null);
    try {
      // 使用兴趣网络 API（返回 nodes 和 edges 格式）
      const response = await apiRequest('get', '/user/interest-graph/network');
      console.log('[兴趣图谱] 获取到的数据:', response);

      // 处理后端返回的数据
      let nodesData = [];
      let edgesData = [];

      // 尝试不同的响应结构
      if (response && response.nodes) {
        nodesData = response.nodes || [];
        edgesData = response.edges || [];
      } else if (response && response.data) {
        if (Array.isArray(response.data)) {
          nodesData = response.data;
        } else if (response.data.nodes) {
          nodesData = response.data.nodes || [];
          edgesData = response.data.edges || [];
        }
      } else if (Array.isArray(response)) {
        nodesData = response;
      }

      // 转换为 Cytoscape 格式
      const elements = nodesData.map((item, index) => {
        const id = item.id || item.link || `node-${index}`;
        const label = item.label || item.title || item.name || `Node ${index}`;

        return {
          data: {
            id,
            label,
            score: item.score || item.hot_score || item.weight || 0,
            category: item.category || item.entity_type || 'default',
            url: item.link || item.url || '#',
          },
        };
      });

      setGraphData({ nodes: elements, edges: edgesData });
      setStats({
        totalNodes: elements.length,
        totalEdges: edgesData.length,
      });
    } catch (err) {
      console.error('[兴趣图谱] 获取数据失败:', err);
      setError('获取兴趣图谱数据失败，请检查后端服务是否正常运行');
      errorToast('获取数据失败，请检查后端服务');
    } finally {
      setLoading(false);
    }
  };

  // 初始化图谱
  useEffect(() => {
    fetchGraphData();
  }, []);

  // 渲染图谱
  useEffect(() => {
    if (graphData.nodes.length > 0 && cyContainerRef.current) {
      // 动态导入 Cytoscape
      import('cytoscape').then((cytoscape) => {
        const cy = cytoscape.default({
          container: cyContainerRef.current,
          elements: [...graphData.nodes, ...graphData.edges],
          style: [
            {
              selector: 'node',
              style: {
                'background-color': (ele) => {
                  const score = parseFloat(ele.data('score')) || 0;
                  // 根据分数设置颜色
                  if (score > 0.8) return '#e85d3f'; // 高热度 - 橙红色
                  if (score > 0.6) return '#fd79a8'; // 中高热度 - 粉色
                  if (score > 0.4) return '#6c5ce7'; // 中热度 - 紫色
                  return '#74b9ff'; // 低热度 - 蓝色
                },
                'label': 'data(label)',
                'text-valign': 'center',
                'text-halign': 'center',
                'color': '#fff',
                'font-size': '11px',
                'width': (ele) => {
                  const score = parseFloat(ele.data('score')) || 0;
                  return 30 + score * 20; // 分数越高节点越大
                },
                'height': (ele) => {
                  const score = parseFloat(ele.data('score')) || 0;
                  return 30 + score * 20;
                },
                'border-width': 2,
                'border-color': '#fff',
              },
            },
            {
              selector: 'edge',
              style: {
                'width': 1,
                'line-color': '#ddd',
                'target-arrow-color': '#ddd',
                'target-arrow-shape': 'triangle',
                'curve-style': 'bezier',
              },
            },
            {
              selector: 'node:selected',
              style: {
                'border-width': 4,
                'border-color': '#00b894',
                'background-color': '#00b894',
              },
            },
          ],
          layout: {
            name: 'cose', // 力导向布局
            animate: true,
            animationDuration: 1000,
            fit: true,
            padding: 50,
            randomize: false,
            componentSpacing: 100,
            nodeOverlap: 20,
            idealEdgeLength: 100,
            edgeElasticity: 100,
            nestingFactor: 5,
            gravity: 80,
            numIter: 1000,
            initialTemp: 200,
            coolingFactor: 0.99,
            minEnergyThreshold: 1e-8,
          },
          minZoom: 0.5,
          maxZoom: 3,
          wheelSensitivity: 0.3,
        });

        // 节点点击事件
        cy.on('tap', 'node', function (evt) {
          const node = evt.target;
          const data = node.data();
          setSelectedNode(data);
          console.log('[兴趣图谱] 点击节点:', data);
        });

        // 点击空白处取消选中
        cy.on('tap', function (evt) {
          if (evt.target === cy) {
            setSelectedNode(null);
          }
        });

        // 节点双击打开链接
        cy.on('dblclick', 'node', function (evt) {
          const node = evt.target;
          const url = node.data('url');
          if (url && url !== '#') {
            window.open(url, '_blank');
          }
        });
      }).catch((err) => {
        console.error('[兴趣图谱] 加载 Cytoscape 失败:', err);
        setError('加载可视化组件失败，请确保已安装 cytoscape');
      });
    }
  }, [graphData]);

  const handleGoBack = () => {
    window.location.href = '/admin';
  };

  return (
    <div className="App">
      <header className="App-header">
        <div className="header-content">
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <h1>Lumos 管理后台</h1>
            <span style={{ color: 'rgba(255,255,255,0.65)' }}>/</span>
            <span style={{ color: 'rgba(255,255,255,0.85)' }}>兴趣图谱</span>
          </div>
          <div className="header-actions">
            <button onClick={fetchGraphData} disabled={loading} className="btn btn-outline" style={{ marginRight: '10px' }}>
              {loading ? '刷新中...' : '🔄 刷新'}
            </button>
            <button onClick={handleGoBack} className="btn btn-outline">
              ← 返回管理后台
            </button>
          </div>
        </div>
      </header>

      <main className="App-main" style={{ padding: '0', overflow: 'hidden' }}>
        <div style={{ display: 'flex', height: 'calc(100vh - 140px)' }}>
          {/* 左侧图谱区域 */}
          <div style={{ flex: 1, position: 'relative', background: '#f5f5f5' }}>
            {loading && (
              <div style={{
                position: 'absolute',
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
                textAlign: 'center',
                zIndex: 10,
              }}>
                <div className="loading">加载中...</div>
                <p style={{ marginTop: '10px', color: '#666' }}>正在获取兴趣图谱数据</p>
              </div>
            )}

            {error && (
              <div style={{
                position: 'absolute',
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
                textAlign: 'center',
                zIndex: 10,
                padding: '40px',
                background: 'white',
                borderRadius: '12px',
                boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
              }}>
                <div style={{ fontSize: '48px', marginBottom: '16px' }}>⚠️</div>
                <p style={{ color: '#e85d3f', fontWeight: 'bold' }}>{error}</p>
                <button onClick={fetchGraphData} className="btn btn-primary" style={{ marginTop: '16px' }}>
                  重试
                </button>
              </div>
            )}

            {!loading && !error && graphData.nodes.length === 0 && (
              <div style={{
                position: 'absolute',
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
                textAlign: 'center',
                zIndex: 10,
              }}>
                <div style={{ fontSize: '64px', marginBottom: '16px' }}>🕸️</div>
                <p style={{ color: '#666' }}>暂无兴趣图谱数据</p>
                <button onClick={fetchGraphData} className="btn btn-primary" style={{ marginTop: '16px' }}>
                  获取数据
                </button>
              </div>
            )}

            <div
              ref={cyContainerRef}
              style={{ width: '100%', height: '100%' }}
            />
          </div>

          {/* 右侧信息面板 */}
          {selectedNode && (
            <div style={{
              width: '320px',
              background: 'white',
              borderLeft: '1px solid #e0e0e0',
              padding: '24px',
              overflowY: 'auto',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <h3 style={{ margin: 0, fontSize: '18px' }}>节点详情</h3>
                <button
                  onClick={() => setSelectedNode(null)}
                  style={{
                    background: 'none',
                    border: 'none',
                    fontSize: '24px',
                    cursor: 'pointer',
                    color: '#999',
                  }}
                >
                  ×
                </button>
              </div>

              <div style={{ marginBottom: '16px' }}>
                <div style={{ fontSize: '12px', color: '#999', marginBottom: '8px' }}>标题</div>
                <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#2D2D2D' }}>{selectedNode.label}</div>
              </div>

              <div style={{ marginBottom: '16px' }}>
                <div style={{ fontSize: '12px', color: '#999', marginBottom: '8px' }}>热度分数</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <div style={{
                    flex: 1,
                    height: '8px',
                    background: '#f0f0f0',
                    borderRadius: '4px',
                    overflow: 'hidden',
                  }}>
                    <div style={{
                      width: `${Math.min(100, (parseFloat(selectedNode.score) || 0) * 100)}%`,
                      height: '100%',
                      background: selectedNode.score > 0.8 ? '#e85d3f' : selectedNode.score > 0.6 ? '#fd79a8' : selectedNode.score > 0.4 ? '#6c5ce7' : '#74b9ff',
                    }} />
                  </div>
                  <div style={{ fontSize: '14px', fontWeight: 'bold', color: '#2D2D2D' }}>
                    {((parseFloat(selectedNode.score) || 0) * 100).toFixed(0)}分
                  </div>
                </div>
              </div>

              <div style={{ marginBottom: '16px' }}>
                <div style={{ fontSize: '12px', color: '#999', marginBottom: '8px' }}>类别</div>
                <div style={{
                  display: 'inline-block',
                  padding: '4px 12px',
                  background: '#f0f0f0',
                  borderRadius: '12px',
                  fontSize: '13px',
                  color: '#666',
                }}>
                  {selectedNode.category || '未分类'}
                </div>
              </div>

              {selectedNode.url && selectedNode.url !== '#' && (
                <div style={{ marginBottom: '24px' }}>
                  <a
                    href={selectedNode.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn btn-primary"
                    style={{ display: 'block', textAlign: 'center' }}
                  >
                    查看原文 🔗
                  </a>
                </div>
              )}

              <div style={{
                padding: '16px',
                background: '#f9f9f9',
                borderRadius: '8px',
                marginTop: '20px',
              }}>
                <div style={{ fontSize: '12px', color: '#999', marginBottom: '8px' }}>操作提示</div>
                <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '13px', color: '#666' }}>
                  <li>单击节点查看详情</li>
                  <li>双击节点打开原文链接</li>
                  <li>拖拽空白区域移动画布</li>
                  <li>滚动鼠标滚轮缩放视图</li>
                </ul>
              </div>
            </div>
          )}
        </div>
      </main>

      <footer className="App-footer">
        <p>© 2026 Lumos Platform - 兴趣图谱可视化</p>
      </footer>

      <ToastContainer />
    </div>
  );
}

export default InterestGraph;

// 渲染兴趣图谱页面
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<InterestGraph />);
