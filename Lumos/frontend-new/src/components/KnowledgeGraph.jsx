import React, { useState, useEffect } from 'react';
import axios from 'axios';
import cytoscape from 'cytoscape';

function KnowledgeGraph() {
  const [graphElements, setGraphElements] = useState([]);

  useEffect(() => {
    axios.get('http://localhost:5000/api/graph')
      .then(response => {
        // 处理后端返回的数据 - 适配不同的可能数据格式
        let nodesData = [];

        // 尝试不同的响应结构
        if (response.data && response.data.data) {
          // 如果是 { count, data: [...] } 结构
          nodesData = response.data.data;
        } else if (Array.isArray(response.data)) {
          // 如果直接返回数组
          nodesData = response.data;
        } else if (response.data && response.data.nodes) {
          // 如果是 { nodes: [...], edges: [...] } 结构
          nodesData = response.data.nodes || [];
        }

        const elements = nodesData.map((item, index) => ({
          data: {
            id: item.link || `node-${index}`,
            label: item.title || item.name || `Node ${index}`
          }
        }));
        setGraphElements(elements);
      })
      .catch(error => console.error('Error fetching graph data:', error));
  }, []);

  useEffect(() => {
    if (graphElements.length > 0) {
      cytoscape({
        container: document.getElementById('cy'),
        elements: graphElements,
        style: [
          {
            selector: 'node',
            style: {
              'background-color': '#007BFF',
              'label': 'data(label)',
              'text-valign': 'center',
              'color': '#fff',
              'font-size': '12px'
            }
          },
          {
            selector: 'edge',
            style: {
              'width': 3,
              'line-color': '#ddd'
            }
          }
        ],
        layout: {
          name: 'cose', // 使用力导向布局
          animate: true,
          fit: true,
          padding: 30
        }
      });
    }
  }, [graphElements]);

  return (
    <div>
      <h2>Knowledge Graph</h2>
      <div id="cy" style={{ width: '800px', height: '600px', border: '1px solid #ccc' }}></div>
    </div>
  );
}

export default KnowledgeGraph;
