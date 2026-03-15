"""
通义千问（Qwen）大模型集成模块
提供新闻摘要、情感分析、自动分类、话题聚类等功能
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from dashscope import Generation
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)


class QwenAnalyzer:
    """通义千问新闻分析器"""

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 Qwen 分析器

        Args:
            api_key: 阿里云 DashScope API Key，如果不传则从环境变量读取
        """
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY not found. Please set it in .env file")

        logger.info("QwenAnalyzer initialized successfully")

    def _call_qwen(self, prompt: str, max_retries: int = 3) -> Optional[Dict[str, Any]]:
        """
        调用 Qwen API

        Args:
            prompt: 提示词
            max_retries: 最大重试次数

        Returns:
            API 响应结果，失败返回 None
        """
        for attempt in range(max_retries):
            try:
                response = Generation.call(
                    model='qwen-max',
                    prompt=prompt,
                    result_format='message',
                    api_key=self.api_key
                )

                if response.status_code == 200:
                    return response
                else:
                    logger.warning(f"Qwen API call failed: {response.code} - {response.message}")
                    if attempt < max_retries - 1:
                        logger.info(f"Retrying... ({attempt + 1}/{max_retries})")

            except Exception as e:
                logger.error(f"Error calling Qwen API: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying... ({attempt + 1}/{max_retries})")

        logger.error(f"Failed to call Qwen API after {max_retries} retries")
        return None

    def analyze_article(self, title: str, content: str) -> Optional[Dict[str, Any]]:
        """
        完整分析一篇文章（摘要 + 情感 + 分类 + 关键词）

        Args:
            title: 文章标题
            content: 文章内容

        Returns:
            分析结果字典
        """
        text = f"{title}\n\n{content}" if content else title

        # 限制文本长度，避免超出 token 限制
        if len(text) > 4000:
            text = text[:4000] + "..."

        prompt = f"""请对以下新闻进行深度分析：

{text}

请严格按照以下 JSON 格式输出分析结果（只输出 JSON，不要其他文字）：
{{
  "summary": "100 字以内的精炼摘要，概括核心内容",
  "sentiment": "positive 或 negative 或 neutral",
  "sentiment_confidence": 0.0-1.0 的置信度分数，
  "category": "科技/金融/政策/市场/国际/企业/其他（选最匹配的一个）",
  "keywords": ["关键词 1", "关键词 2", "关键词 3", "关键词 4", "关键词 5"],
  "entities": ["重要实体/公司/人物 1", "实体 2"],
  "hot_potential": "high/medium/low（热点潜力评估）"
}}"""

        response = self._call_qwen(prompt)
        if not response:
            return None

        try:
            # 解析 JSON 结果
            result_text = response.output.choices[0].message.content.strip()

            # 处理可能的 markdown 代码块标记
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            result_text = result_text.strip()

            result = json.loads(result_text)

            # 标准化输出格式
            return {
                "summary": result.get("summary", ""),
                "sentiment": result.get("sentiment", "neutral"),
                "sentiment_confidence": float(result.get("sentiment_confidence", 0.5)),
                "category": result.get("category", "其他"),
                "keywords": result.get("keywords", []),
                "entities": result.get("entities", []),
                "hot_potential": result.get("hot_potential", "medium")
            }

        except (json.JSONDecodeError, IndexError, KeyError) as e:
            logger.error(f"Error parsing Qwen response: {e}")
            logger.debug(f"Raw response: {response.output.choices[0].message.content if response.output else 'No output'}")
            return None

    def summarize(self, text: str, max_length: int = 100) -> Optional[str]:
        """
        生成文本摘要

        Args:
            text: 输入文本
            max_length: 最大长度

        Returns:
            摘要字符串
        """
        if len(text) > 3000:
            text = text[:3000] + "..."

        prompt = f"""请将以下文本概括为{max_length}字以内的摘要，要求精炼准确：

{text}

只输出摘要内容，不要其他文字。"""

        response = self._call_qwen(prompt)
        if response:
            return response.output.choices[0].message.content.strip()
        return None

    def sentiment_analysis(self, text: str) -> Optional[Dict[str, Any]]:
        """
        情感分析

        Args:
            text: 输入文本

        Returns:
            情感分析结果 {sentiment: str, confidence: float}
        """
        if len(text) > 2000:
            text = text[:2000] + "..."

        prompt = f"""请对以下文本进行情感分析：

{text}

请严格按照以下 JSON 格式输出（只输出 JSON）：
{{
  "sentiment": "positive 或 negative 或 neutral",
  "confidence": 0.0-1.0 的置信度分数,
  "reason": "一句话解释判断理由"
}}"""

        response = self._call_qwen(prompt)
        if not response:
            return None

        try:
            result = json.loads(response.output.choices[0].message.content.strip())
            return {
                "sentiment": result.get("sentiment", "neutral"),
                "confidence": float(result.get("confidence", 0.5)),
                "reason": result.get("reason", "")
            }
        except (json.JSONDecodeError, KeyError):
            return None

    def classify(self, text: str) -> Optional[str]:
        """
        文本分类

        Args:
            text: 输入文本

        Returns:
            分类标签
        """
        if len(text) > 2000:
            text = text[:2000] + "..."

        prompt = f"""请判断以下新闻的分类：

{text}

分类选项：科技/金融/政策/市场/国际/企业/其他
只输出分类名称，不要其他文字。"""

        response = self._call_qwen(prompt)
        if response:
            return response.output.choices[0].message.content.strip()
        return None

    def cluster_topics(self, articles: List[Dict[str, str]]) -> Optional[List[Dict[str, Any]]]:
        """
        话题聚类分析

        Args:
            articles: 文章列表，每项包含 title 和 content

        Returns:
            聚类结果
        """
        # 构建输入文本
        articles_text = ""
        for i, article in enumerate(articles[:20], 1):  # 限制最多 20 篇
            title = article.get("title", "")
            content = article.get("content", "")[:200]
            articles_text += f"{i}. {title}\n{content}\n\n"

        prompt = f"""请分析以下新闻列表，识别相关话题和潜在热点事件：

{articles_text}

请严格按照以下 JSON 格式输出：
{{
  "topics": [
    {{
      "name": "话题名称",
      "article_ids": [1, 2, 3],
      "description": "话题描述",
      "hot_level": "high/medium/low"
    }}
  ],
  "trending_events": [
    {{
      "event": "潜在热点事件描述",
      "related_articles": [1, 2],
      "confidence": 0.8
    }}
  ]
}}

只输出 JSON，不要其他文字。"""

        response = self._call_qwen(prompt)
        if not response:
            return None

        try:
            result = json.loads(response.output.choices[0].message.content.strip())
            return result
        except (json.JSONDecodeError, KeyError):
            return None


# 便捷函数
def get_analyzer() -> QwenAnalyzer:
    """获取 QwenAnalyzer 实例"""
    return QwenAnalyzer()


if __name__ == "__main__":
    # 测试代码
    analyzer = get_analyzer()

    test_title = "AI 大模型竞争白热化，多家厂商发布新产品"
    test_content = """
    近日，多家 AI 厂商密集发布新一代大模型产品。阿里巴巴通义千问发布了 Qwen-2.5 版本，
    在多项基准测试中表现优异。百度文心一言也宣布了新功能升级。业界分析认为，
    这标志着大模型行业竞争进入新阶段，技术迭代速度加快，应用场景不断拓展。
    预计未来几个月将有更多厂商跟进发布新品。
    """

    print("测试文章分析...")
    result = analyzer.analyze_article(test_title, test_content)
    if result:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("分析失败")
