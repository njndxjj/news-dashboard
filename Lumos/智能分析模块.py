# 智能分析模块实现

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter
import nltk
from nltk.corpus import stopwords
import spacy

nltk.download('stopwords')
nlp = spacy.load("en_core_web_sm")

# 示例数据
articles = [
    "特斯拉正在扩展其电池业务。",
    "新能源汽车销量增长迅速。",
    "特斯拉推出了新车型。"
]
user_interest = "特斯拉 销量 电池"

# 1. 关键词提取方法
stop_words = set(stopwords.words('english'))
def extract_keywords(text, top_n=3):
    words = [token.text for token in nlp(text.lower()) if token.is_alpha and token.text not in stop_words]
    keyword_freq = Counter(words)
    return keyword_freq.most_common(top_n)

# 2. 个性化推荐
vectorizer = TfidfVectorizer()
article_vectors = vectorizer.fit_transform(articles)
user_vector = vectorizer.transform([user_interest])

# 相似度计算
def recommend_articles():
    similarities = cosine_similarity(user_vector, article_vectors)
    rankings = similarities[0].argsort()[::-1]  # 按相似度降序排列索引
    recommendations = [(articles[idx], similarities[0][idx]) for idx in rankings]
    return recommendations

# 3. 汇总社交分析（互动量、病毒传播、情感分析）
def social_analysis_demo():
    return {
        "总互动量": 128300,
        "病毒传播": 4,
        "情感倾向": "正面",
        "传播速度": "极快"
    }

# 调用示例功能
keywords = extract_keywords("特斯拉在全球销量提升的背景下，其电池业务也取得突破性进展。")
recommendations = recommend_articles()
social_analysis = social_analysis_demo()

# 打印结果
print("关键词: ", keywords)
print("推荐文章: ", recommendations)
print("社交分析: ", social_analysis)