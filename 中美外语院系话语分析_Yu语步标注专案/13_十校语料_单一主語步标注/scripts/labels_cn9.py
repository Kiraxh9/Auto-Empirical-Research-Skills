# -*- coding: utf-8 -*-
"""9 所既有语料：单一主語步终判（默认沿用原嵌套标注的「外层主語步」，仅对违反手册判据者修正）。"""
CORRECTIONS = {
    'Beijing Normal University.txt': {},
    'China Agricultural University.txt': {},
    'Chongqing University.txt': {6: 'M01'},          # 研究中心+7个研究所 = 组织架构 (M01-S2)
    'East China Normal University.txt': {4: 'M05', 49: 'M05'},  # 学位点设置 / 学科体系完备
    'Fudan University.txt': {},
    'Harbin Institute of Technology.txt': {},
    'Huazhong University of Science and Technology.txt': {36: 'M01', 37: 'M10'},  # 学生会组织 / 学生活动动态
    'Central South University.txt': {72: 'M05', 114: 'M07', 123: 'M05'},
    'Dalian University of Technology.txt': {85: 'M07', 154: 'M07'},
}
