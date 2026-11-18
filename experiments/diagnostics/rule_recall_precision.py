# -*- coding: utf-8 -*-
"""评估高危规则引擎在标注集上的查全/查准（只读）。"""
import pandas as pd
import sys
sys.path.append('src')
from agent_router import HIGH_RISK_KEYWORDS

df = pd.read_csv('data/annotations.csv', encoding='utf-8-sig')
hit = df.raw_text.apply(lambda t: any(k in str(t) for k in HIGH_RISK_KEYWORDS))
gold = df.high_risk_gold == 1

tp = int((hit & gold).sum())
fn = int((~hit & gold).sum())
fp = int((hit & ~gold).sum())
tn = int((~hit & ~gold).sum())
print(f'gold高危={int(gold.sum())}  规则命中={int(hit.sum())}')
print(f'TP={tp} FN={fn} FP={fp} TN={tn}')
print(f'查全率(recall) = {tp/(tp+fn):.3f}')
print(f'查准率(precision) = {tp/(tp+fp):.3f}')
print('\n漏报样例:')
for t in df[gold & ~hit].raw_text.head(6):
    print('  ', t)
print('\n误报样例:')
for t in df[~gold & hit].raw_text.head(6):
    print('  ', t)
