# -*- coding: utf-8 -*-
"""验证集上的特征/超参对比（只读，用于报告 3.2 的选型依据）。"""
import pandas as pd
import re
import jieba
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score


def clean(t):
    c = re.sub(r'[^\u4e00-\u9fa5]', '', str(t))
    c = re.sub(r'[一二三四五六七八九十]+[号栋楼区层]', '', c)
    for w in ['你好', '您好', '麻烦', '请', '谢谢', '急', '帮', '帮忙', '报修', '有个', '一个', '这里', '那里']:
        c = c.replace(w, '')
    return c.strip()


df = pd.read_csv('data/annotations.csv', encoding='utf-8-sig')
tr = df[df.split == 'train']
va = df[df.split == 'val']

Xtr_raw = [clean(t) for t in tr.raw_text]
Xva_raw = [clean(t) for t in va.raw_text]
Xtr_word = [' '.join(jieba.cut(t)) for t in Xtr_raw]
Xva_word = [' '.join(jieba.cut(t)) for t in Xva_raw]

configs = [
    ('word 1-2gram, C=1', Xtr_word, Xva_word, dict(analyzer='word', ngram_range=(1, 2), max_features=5000), 1.0),
    ('char 1-3gram, C=1', Xtr_raw, Xva_raw, dict(analyzer='char', ngram_range=(1, 3), max_features=5000), 1.0),
    ('char 1-3gram, C=10', Xtr_raw, Xva_raw, dict(analyzer='char', ngram_range=(1, 3), max_features=5000), 10.0),
]

for name, xtr, xva, kw, C in configs:
    v = TfidfVectorizer(**kw)
    A = v.fit_transform(xtr)
    B = v.transform(xva)
    m = LogisticRegression(C=C, class_weight='balanced', max_iter=1000, random_state=42).fit(A, tr.facility_label)
    f1 = f1_score(va.facility_label, m.predict(B), average='macro')
    print(f'{name:24s} val MacroF1 = {f1:.4f}   特征维度={A.shape[1]}')
