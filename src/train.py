import pandas as pd
import jieba
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, f1_score
import joblib
import os

def clean_text_for_ml(text):
    clean = re.sub(r'[^\u4e00-\u9fa5]', '', str(text))
    clean = re.sub(r'[一二三四五六七八九十]+[号栋楼区层]', '', clean)
    stop_words = ["你好", "您好", "麻烦", "请", "谢谢", "急", "帮", "帮忙", "报修", "有个", "一个", "这里", "那里"]
    for word in stop_words:
        clean = clean.replace(word, "")
    return clean.strip()

def main():
    print("1. 加载数据...")
    df = pd.read_csv("data/annotations.csv", encoding="utf-8-sig")
    train_df = df[df['split'] == 'train']
    test_df = df[df['split'] == 'test']
    
    print("2. 文本特征提取...")
    train_texts = [clean_text_for_ml(t) for t in train_df['raw_text']]
    test_texts = [clean_text_for_ml(t) for t in test_df['raw_text']]
    
    # 使用字符级特征
    vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(1, 3), max_features=5000)
    X_train = vectorizer.fit_transform(train_texts)
    X_test = vectorizer.transform(test_texts)
    
    y_train = train_df['facility_label']
    y_test = test_df['facility_label']
    
    print("3. 训练与评估逻辑回归...")
    # 🌟 关键修改：将 C 参数从默认的 1.0 调大到 10.0
    lr_model = LogisticRegression(C=10.0, class_weight='balanced', max_iter=1000, random_state=42)
    lr_model.fit(X_train, y_train)
    lr_pred = lr_model.predict(X_test)
    
    print(f"\n[主模型] 逻辑回归 Macro F1: {f1_score(y_test, lr_pred, average='macro'):.4f}")

    os.makedirs("models", exist_ok=True)
    joblib.dump(vectorizer, "models/vectorizer.pkl")
    joblib.dump(lr_model, "models/lr_model.pkl")
    print("\n✅ 真实模型已重新训练并保存！请重启 Streamlit。")

if __name__ == "__main__":
    main()