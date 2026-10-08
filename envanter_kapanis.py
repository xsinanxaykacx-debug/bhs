# -*- coding: utf-8 -*-
import pandas as pd
import os

files = ['E0.csv', 'E0 (1).csv', 'E0 (2).csv', 'E0 (3).csv', 'E0 (4).csv',
         'E0 (5).csv', 'E0 (6).csv', 'E0 (7).csv', 'E0 (8).csv', 'E0 (9).csv']
seasons = ['2015/16', '2016/17', '2017/18', '2018/19', '2019/20',
           '2020/21', '2021/22', '2022/23', '2023/24', '2024/25']

print(f"{'Sezon':10s} {'Dosya':12s} {'B365CH':>8s} {'B365CD':>8s} {'B365CA':>8s} {'Satir':>6s}")
print('-' * 60)

for f, s in zip(files, seasons):
    if not os.path.exists(f):
        print(f"{s:10s} {f:12s} MISSING")
        continue
    df = pd.read_csv(f, encoding='utf-8-sig')
    cols = df.columns.tolist()
    has = lambda c: 'VAR' if c in cols else 'YOK'
    print(f"{s:10s} {f:12s} {has('B365CH'):>8s} {has('B365CD'):>8s} {has('B365CA'):>8s} {len(df):>6d}")