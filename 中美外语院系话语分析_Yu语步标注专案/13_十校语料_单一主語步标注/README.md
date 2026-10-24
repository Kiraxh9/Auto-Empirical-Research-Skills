# 中国 10 所高校外语院系「单一主語步」标注数据集

> **任务**：按 [`07_AI语步标注操作说明_10核心语步标准版.md`](../07_AI语步标注操作说明_10核心语步标准版.md) 与
> [`06_中美高校外语院系_精炼10核心语步编码手册.csv`](../06_中美高校外语院系_精炼10核心语步编码手册.csv)，
> 对 10 份高校外语院系英文「学院简介」全文做 `M01–M10 + <OTHER>` 語步标注。
> **口径要求（本批特色）**：**尽量少标注复合語步——每个单元只赋一个「主導語步」（outer layer only），复合語步率 `0.00%`。**

- 语料规模：`18,595` 词 / `826` 个标注单元 / 10 所学校（含新增 Beihang 语料）
- 有效体裁话语：`18,269` 词（保留率 **`98.25%`**）；`<OTHER>` 纯网页残片 `326` 词（`1.75%`）
- 质检：**逐字符保真 `100%`** + **单标签合法 `100%`** + **标签配平/结构良构 `100%`**

---

## 一、目录结构

```
13_十校语料_单一主語步标注/
├── README.md                          # 本文件：标注口径、判据细则、质检与复现说明
├── 统计报告_10校单一主語步.md           # 逐校语步分布表 + 合并池排序 + 与既有 12 校口径对比
├── 语步统计汇总_10校.csv                # 每校 10 語步词数/占比、OTHER、保留率、H、J、单元数、复合率
├── 逐单元标注明细_10校.csv              # 826 行单元级长表（文件 / 单元号 / 主語步 / 词数 / 文本）
├── 标注后语料/                         # ★ 交付主件：10 份标注全文（一单元一行，单标签）
├── 原始语料/                           # 10 份上传原文备份（供复核比对，未做任何改动）
└── scripts/                           # 可复现流水线
    ├── move_units.py                  # 标注文件解析/写出工具
    ├── segment_beihang.py             # Beihang 原文切分（新语料）
    ├── labels_cn9.py                  # 9 所既有语料的单一主語步终判（含 10 处修正）
    ├── labels_beihang.py              # Beihang 单元合并组 + 主語步终判
    ├── build_annotations.py           # 生成标注文本 / 明细表 / 统计表 + 保真校验
    └── validate.py                    # 独立质检脚本（保真 / 单标签 / 配平 / 良构）
```

复现：

```bash
cd 13_十校语料_单一主語步标注
python3 scripts/build_annotations.py   # 重建 标注后语料/ + 两个 CSV
python3 scripts/validate.py            # 质检（应输出「全部通过」）
```

---

## 二、标注口径

### 2.1 标签集

仅使用 `M01–M10` 与 `<OTHER>`，标签置于每个单元的首尾，例如：

```text
<M02>The predecessor of the School of Foreign Languages and Literature was the English Department of Beijing Normal University founded in 1912, where famous scholars like Lin Yutang and Liang Shiqiu have taught, and alumni Zhou Gucheng and Xiong Shiyi have studied.</M02>
```

### 2.2 单元切分（Unit）规则

| 规则 | 说明 |
| :--- | :--- |
| **U1 一完整句一单元** | 以句号/问号/感叹号结尾的完整句，**不切分词、短语或从句**；标签只出现在句首与句末 |
| **U2 整体块一单元** | 地址/电话/邮箱块、领导与行政名录块、教职工/学生名录块、课程列表块、奖项列表块等，**连同其栏目标题整体封装**，不拆成裸姓名/裸课程行 |
| **U3 纯结构残片** | 孤立栏目名（`Overview`、`Department of German`、`MORE INFO`、`Authored by …`、`Name/Position/Email Address` 之类）单独成单元并标 `<OTHER>` |
| **U4 原文零改写** | 拼写、标点、乱码（如 `??`、`?¡ã`）、`&`、`|` 等一律逐字符保留；校验以「剥离标签后与原文完全一致」为准 |

### 2.3 「少复合語步」的判定：單一主導語步

每个单元只保留**在实际语境中占主导交际目的**的那一个語步；原手册允许的 `<MXX><MYY>…</MYY></MXX>` 复合式在本批语料中**一律不使用**，因此：

- 复合語步单元数 `0`，复合語步率 `0.00%`（可直接作为「主導語步唯一化」的对照条件）；
- 若某单元含两个共等命题，按下列优先序判定主導語步（与手册边界判据一致）：
  `M02 历时事件 > M07 当下成就`、`M05 在校培养 > M07 毕业去向`、`M06 静态投入 > M07 已获荣誉`、
  `M01 人员组成 > M10 联系方式`、`M03 抽象承诺 > M05 具体课程`、`M10 硬性规程 > M05 项目介绍`。

### 2.4 关键边界判据（本批评分细则，含对既有标注的修正）

| 编号 | 判据 | 依据 |
| :--- | :--- | :--- |
| **R1** | **带邮箱/电话/办公室的联系人卡片**（如 HIT 领导名录的 `Contact information:` 行、DUT 领导 `Tel/Email` 行）→ `M10`；**同一人名但只列职务与分工、无联系方式**（如 `Position: … Division of work: …`）→ `M01` | 手册 M01/M10 边界 |
| **R2** | **人员/学生组成名录块**（Faculty Members、Professors、Administration 职务表等）→ `M01`，并与栏目标题整体封装；但名录中**含邮箱/电话的表格行**按 R1 归 `M10` | 手册 M01-S3 |
| **R3** | **研究中心/研究所/研究基地**：作为**内部组织架构**列举（`consists of … research centers`、`a Research Center … in which there are 7 research institutes`）→ `M01`；作为**科研平台与支撑资源**列举（`boasts eight study centers`、`research bases and think tanks`、`houses a range of advanced teaching and research facilities`）→ `M06`；**学者的研究领域列表**（`Research fields include …`、`Faculty by Area of Study`）→ `M04` | 手册 M01-S2 / M06-S2 / M04-S2 |
| **R4** | **带年份的事件**（成立于、获批学位点、合并更名、迁址）→ `M02`；**同一事项以「now offers / currently runs」陈述现状**→ `M05` | 手册 M02/M05 |
| **R5** | **`only / very few / the first / leading / top` 等独特性与领先性断言** → `M07`（含 Beihang「the only known rhetoric department in China」） | 手册 M07-S1/S2 |
| **R6** | **硬性学分/考试/毕业要求**（`38 course credits`、`pass CATTI 2 before graduation`、`finish a research paper of 20,000 words`、`if they have obtained 30 course credits`）→ `M10` | 手册 M10-S2 |
| **R7** | **学生社团、学生会、图书馆、教学楼、奖学金与师生比等** → `M06`（办学支撑条件）；学生组织自身的活动报道 → `M10` | 手册 M06/M10-S3 |
| **R8** | **国际化/合作**（海外交换、2+2/3+1、暑期营、外专授课、邀请讲座、国际会议、实习基地协议）→ `M08` | 手册 M08-S1/S2 |
| **R9** | **欢迎/邀请/加入/捐赠致谢**（`We welcome …`、`welcomes prospective students to join the warm family`）→ `M09`；无谓语孤立栏目词（`MORE INFO`、`Courses Offered:`）→ `<OTHER>` | 手册 M09/OTHER |
| **R10** | **师资总人数、职称结构、学历比例、外教人数**→ `M06`；**由师资获得的奖项/头衔**→ `M07`（若同句只报职称结构并顺带列头衔，取 `M06`） | 手册 M06/M07 |

---

## 三、两批语料的处理路径

| 批次 | 学校 | 处理方式 |
| :--- | :--- | :--- |
| **A. 既有语料（9 所）** | 北京师范大学、中南大学、中国农业大学、重庆大学、大连理工大学、华东师范大学、复旦大学、哈尔滨工业大学、华中科技大学 | 沿用本项目已确立的**单元切分**（已核验与上传原文逐字符一致），逐单元**重新裁定单一主導語步**：以原嵌套标注的**外层語步**为基础，按 R1–R10 复核后**修正 10 个单元**（见下表） |
| **B. 新语料（1 所）** | **Beihang University (former BUAA)**（原北京航空航天大学，`3,946` 词、`194` 单元） | **全新标注**：先按 U1–U4 自动切分，再人工合并名录/课程/地址块，逐单元赋 `M01–M10/OTHER` |

### 3.1 修正清单（10 个单元）

| 文件 | 单元号 | 原文要点 | 原外层标签 | 终判 | 理由 |
| :--- | ---: | :--- | :---: | :---: | :--- |
| Chongqing University | 6 | `established a Research Center … in which there are 7 research institutes` | `M06` | `M01` | R3 组织架构 |
| East China Normal University | 4 | `We set up a doctoral program … in 1998 and … in 2006`（学位点设置清单） | `M02` | `M05` | R4 现状供给、与相邻学位点列举同质 |
| East China Normal University | 49 | `These programs showcase the school's full-fledged discipline system.` | `M07` | `M05` | 论旨是学科体系完备，非排名/获奖 |
| Huazhong University of Science and Technology | 36 | `The Student Union … aiming at serving for students whole-heartedly …` | `M03` | `M01` | 学生组织性质与沿革 |
| Huazhong University of Science and Technology | 37 | `They had directed the work of its branches … held various activities …` | `M05` | `M10` | 活动开展情况通报（无教学活动） |
| Central South University | 72 | `Practicing the educational philosophy …, the program is committed to cultivating professionals …` | `M03` | `M05` | 专业培养目标承诺 |
| Central South University | 114 | `… which is a first-tier doctoral program and a flagship discipline in Hunan Province.` | `M05` | `M07` | R5 重点学科资质 |
| Central South University | 123 | `Adhering to the mission …, the department is characterized by multilingual integration …` | `M03` | `M05` | 办学特色与培养模式 |
| Dalian University of Technology | 85 | `The teachers … are diligent … and have gained many important achievements.` | `M06` | `M07` | 成就陈述为主 |
| Dalian University of Technology | 154 | `Teachers have attended multiple international academic conferences, with … articles published.` | `M08` | `M07` | 成果产出为主，非合作关系 |

---

## 四、质检结果

`python3 scripts/validate.py` 输出（10 份文件全部通过）：

| 文件 | 单元数 | 单标签合法 | 结构良构 | 逐字符保真 |
| :--- | ---: | :---: | :---: | :---: |
| Beihang University (former BUAA).txt | 194 | PASS | PASS | PASS |
| Beijing Normal University.txt | 17 | PASS | PASS | PASS |
| Central South University.txt | 149 | PASS | PASS | PASS |
| China Agricultural University.txt | 5 | PASS | PASS | PASS |
| Chongqing University.txt | 13 | PASS | PASS | PASS |
| Dalian University of Technology.txt | 204 | PASS | PASS | PASS |
| East China Normal University.txt | 50 | PASS | PASS | PASS |
| Fudan University.txt | 53 | PASS | PASS | PASS |
| Harbin Institute of Technology.txt | 59 | PASS | PASS | PASS |
| Huazhong University of Science and Technology.txt | 82 | PASS | PASS | PASS |
| **合计** | **826** | **100%** | **100%** | **100%** |

> 结构良构校验：因原文 `&`（如 `Language Cognition & Language Application`）按 U4 逐字符保留，解析时需先将裸 `&` 转义为 `&amp;`；`validate.py` 已按此处理。
> 复合語步：全库 `0` 个（`<Mxx><Myy>…` 形式出现次数 `0`）。

---

## 五、统计要点（详见 `统计报告_10校单一主語步.md`）

10 校合并池（词数加权，`18,269` 有效词）：

| 語步 | M01 | M02 | M03 | M04 | M05 | M06 | M07 | M08 | M09 | M10 |
| :---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 占比 | 7.30% | 15.47% | 3.68% | 2.88% | **24.62%** | 14.93% | 21.51% | 6.33% | 0.28% | 2.99% |

- **培养（`M05`）+ 实绩（`M07`）+ 师资（`M06`）** 合计 `61.06%`，构成中国高校「学院简介」的三大主柱；
- **历史开篇（`M02`）** 稳定处于高位（`15.47%`，复旦 `47.87%`、华东师大 `27.82%`），与 RQ1「中国高校倾向以历史沿革开篇」的假设一致；
- **学科价值论证（`M04`）** 仅 `2.88%`，且集中于以科研为导向的 Beihang、复旦、大连理工；
- **读者互动/募捐（`M09`）** 近乎缺席（`0.28%`，仅 Beihang 的 2 处欢迎语），与美式语料形成鲜明对照；
- 香农熵 `H = 1.959`、均匀度 `J = 0.851`（`CMU` 为 `J = 0.927`），说明单校語步配置高度集中于少数語步。

---

## 六、数据使用

- `逐单元标注明细_10校.csv`（UTF-8-BOM，Excel 直开）为**单元级长表**，可直接做 RQ1–RQ5 的混合效应/卡方/对应分析；
- `语步统计汇总_10校.csv` 末行为 `CN_10_SUM（10所中国高校合并池）`，可直接与 [`11_…10语步分布统计汇总矩阵.csv`](../11_已标注12所高校_10语步分布统计汇总矩阵.csv) 的美国样本（`F06`）并表；
- 需要恢复复合語步信息时，可对照 [`../中国大学/`](../中国大学) 中的嵌套标注版本（9 校）与本目录 `标注后语料/` 的单一主導語步版本。

> **引用口径**：語步体系来自 Yu (2023, *IEEE TPC*) 与 Yu, Yu, Bondi & Hyland (2026, *RMAL*, Appendix 1)；
> 本批数据额外声明「单一主導語步、复合語步率 0%」的标注条件，与嵌套多标签版本不可直接混池比较。
