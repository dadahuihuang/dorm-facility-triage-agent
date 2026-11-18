# -*- coding: utf-8 -*-
import pandas as pd
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import f1_score


def clean(t):
    c = re.sub(r'[^\u4e00-\u9fa5]', '', str(t))
    c = re.sub(r'[一二三四五六七八九十]+[号栋楼区层]', '', c)
    for w in ['你好', '您好', '麻烦', '请', '谢谢', '急', '帮', '帮忙', '报修', '有个', '一个', '这里', '那里']:
        c = c.replace(w, '')
    return c.strip()


df = pd.read_csv('data/annotations.csv', encoding='utf-8-sig')
tr, te = df[df.split == 'train'], df[df.split == 'test']

for tag, fn in [('原始文本-不清洗', lambda s: str(s)), ('正则清洗后', clean)]:
    v = TfidfVectorizer(analyzer='char', ngram_range=(1, 3), max_features=5000)
    A = v.fit_transform([fn(t) for t in tr.raw_text])
    B = v.transform([fn(t) for t in te.raw_text])
    lr = LogisticRegression(C=10.0, class_weight='balanced', max_iter=1000, random_state=42).fit(A, tr.facility_label)
    nb = MultinomialNB().fit(A, tr.facility_label)
    lr_f1 = f1_score(te.facility_label, lr.predict(B), average='macro')
    nb_f1 = f1_score(te.facility_label, nb.predict(B), average='macro')
    print(f'{tag}: LR={lr_f1:.4f}  NB={nb_f1:.4f}')
