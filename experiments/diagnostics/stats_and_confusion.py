# -*- coding: utf-8 -*-
"""为报告修订生成可核对的统计与混淆矩阵（只读，不改任何数据）。"""
import pandas as pd
import numpy as np
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, f1_score


def clean(t):
    c = re.sub(r'[^\u4e00-\u9fa5]', '', str(t))
    c = re.sub(r'[一二三四五六七八九十]+[号栋楼区层]', '', c)
    for w in ['你好', '您好', '麻烦', '请', '谢谢', '急', '帮', '帮忙', '报修', '有个', '一个', '这里', '那里']:
        c = c.replace(w, '')
    return c.strip()


df = pd.read_csv('data/annotations.csv', encoding='utf-8-sig')
print('总数', len(df))
print('split', df.split.value_counts().to_dict())
print('source', df.source_type.value_counts().to_dict())
print('high_risk', int(df.high_risk_gold.sum()))
print()
print(pd.crosstab(df.facility_label, df.split))

tr, te = df[df.split == 'train'], df[df.split == 'test']
v = TfidfVectorizer(analyzer='char', ngram_range=(1, 3), max_features=5000)
A = v.fit_transform([clean(t) for t in tr.raw_text])
B = v.transform([clean(t) for t in te.raw_text])
lr = LogisticRegression(C=10.0, class_weight='balanced', max_iter=1000, random_state=42).fit(A, tr.facility_label)
pred = lr.predict(B)
print('\nmacroF1 %.4f' % f1_score(te.facility_label, pred, average='macro'))
labels = sorted(df.facility_label.unique())
cm = confusion_matrix(te.facility_label, pred, labels=labels)
print('labels', labels)
print(cm)
print('\n错分样本:')
proba = lr.predict_proba(B)
for i, (t, p) in enumerate(zip(te.facility_label.values, pred)):
    if t != p:
        conf = proba[i][list(lr.classes_).index(p)]
        print(f'  true={t} pred={p} conf={conf:.3f} | {te.raw_text.values[i]}')
