# -*- coding: utf-8 -*-
"""一键复算报告中的全部指标，写出 experiments/results.csv。

用法：python experiments/build_results.py
"""
import os
import re
import sys

import pandas as pd
import jieba
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.naive_bayes import MultinomialNB

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))


def clean(t):
    c = re.sub(r'[^\u4e00-\u9fa5]', '', str(t))
    c = re.sub(r'[一二三四五六七八九十]+[号栋楼区层]', '', c)
    for w in ['你好', '您好', '麻烦', '请', '谢谢', '急', '帮', '帮忙', '报修', '有个', '一个', '这里', '那里']:
        c = c.replace(w, '')
    return c.strip()


def run(df, split, model_name, analyzer, C, use_clean):
    tr = df[df.split == 'train']
    ev = df[df.split == split]
    fn = clean if use_clean else (lambda s: str(s))
    if analyzer == 'word':
        fn_tr = lambda s: ' '.join(jieba.cut(fn(s)))  # noqa: E731
        fn_ev = fn_tr
    else:
        fn_tr, fn_ev = fn, fn

    vec = TfidfVectorizer(analyzer=analyzer, ngram_range=(1, 3) if analyzer == 'char' else (1, 2),
                          max_features=5000)
    A = vec.fit_transform([fn_tr(t) for t in tr.raw_text])
    B = vec.transform([fn_ev(t) for t in ev.raw_text])

    if model_name == 'NB':
        m = MultinomialNB()
    else:
        m = LogisticRegression(C=C, class_weight='balanced', max_iter=1000, random_state=42)
    m.fit(A, tr.facility_label)
    pred = m.predict(B)
    return dict(
        split=split,
        model=model_name,
        features=f'{analyzer} 1-{3 if analyzer=="char" else 2}gram',
        cleaning='是' if use_clean else '否',
        C=C if model_name == 'LR' else '',
        macro_f1=round(f1_score(ev.facility_label, pred, average='macro'), 4),
        accuracy=round(accuracy_score(ev.facility_label, pred), 4),
        n_features=A.shape[1],
        n_eval=len(ev),
    )


def main():
    df = pd.read_csv(os.path.join(ROOT, 'data', 'annotations.csv'), encoding='utf-8-sig')
    rows = [
        run(df, 'test', 'NB', 'char', '', False),
        run(df, 'test', 'NB', 'char', '', True),
        run(df, 'test', 'LR', 'char', 10.0, False),
        run(df, 'test', 'LR', 'char', 10.0, True),
        run(df, 'val', 'LR', 'word', 1.0, True),
        run(df, 'val', 'LR', 'char', 1.0, True),
        run(df, 'val', 'LR', 'char', 10.0, True),
    ]
    out = pd.DataFrame(rows)
    out.insert(0, 'exp_id', [f'E{i}' for i in range(1, len(out) + 1)])
    path = os.path.join(ROOT, 'experiments', 'results.csv')
    out.to_csv(path, index=False, encoding='utf-8-sig')
    print(out.to_string(index=False))
    print('\n已写入', path)


if __name__ == '__main__':
    main()
