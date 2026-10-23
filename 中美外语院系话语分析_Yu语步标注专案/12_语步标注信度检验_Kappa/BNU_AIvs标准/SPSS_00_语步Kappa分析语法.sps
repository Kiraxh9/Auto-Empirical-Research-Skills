* Encoding: UTF-8.
* =============================================================================
*  语步标注一致性检验（Cohen's Kappa）—— SPSS 语法包
* =============================================================================
*  配对语料 ：北京师范大学 F02「学院简介」
*  标注者 A ：AI 嵌套标注   —— 主语步取"嵌套外层"；"嵌套内层"记为子语步
*  标注者 B ：标准标注       —— 扁平单标签，每单元仅一个语步
*  分析单元 ：N = 17 个语段（按语段文本逐条对齐，100% 文本一致）
*  类目体系 ：M01–M10 + OTHER，共 11 类（见"语步编码本"）
*
*  预期结果（Python 独立复核，用于校验 SPSS 输出是否一致）：
*      Po = .8824     Pe = .1730
*      Kappa = .8577  ASE = .0925   95%CI [.6765, 1.000]   p < .001
*      判读：Landis & Koch (1977) "几乎完美 Almost perfect"
*
*  【三条最容易踩的坑，务必先读】
*    1. 必须用【数值编码变量】（*_Code / *_Flag），不要用 M01/OTHER 这类字符串变量。
*       SPSS 规定：参与 Kappa 的两个变量存储类型必须一致；若都是字符串，
*       还要求"定义长度"完全相同（"M01" 长 3、"OTHER" 长 5），否则一律不计算 Kappa。
*    2. 两个变量的取值集合必须完全对称（表格必须是方阵），否则 SPSS 报
*       "Kappa statistics cannot be computed. The table is not square."。
*       本例 OTHER 只被 A 用了 1 次、B 从未使用，因此已在本数据包里预先
*       用 0.0001 的极小权重补齐（变量 W_forKappa），直接 WEIGHT BY 即可。
*    3. 权重要记得关（WEIGHT OFF），否则后续所有分析都会被放大 17 倍。
* =============================================================================.


* =============================================================================
*  第 0 步：把下面三行的 NAME 改成你本机的实际路径（要写到文件名，含 .sav）
*          路径中若含中文，请确保 SPSS 处于 Unicode 模式（默认即 Unicode）。
*          如遇路径乱码，可把整个文件夹拷到纯英文目录下再改路径。
* =============================================================================.
FILE HANDLE f01 /NAME = 'D:\语步标注Kappa\BNU_AIvs标准\SPSS_01_主数据_每单元一行.sav'.
FILE HANDLE f02 /NAME = 'D:\语步标注Kappa\BNU_AIvs标准\SPSS_02_频数加权表_AxB.sav'.
FILE HANDLE f03 /NAME = 'D:\语步标注Kappa\BNU_AIvs标准\SPSS_03_逐语步二分长表.sav'.


* #############################################################################
*  路线 A（推荐）：频数加权表  →  整体 Cohen's Kappa
* -----------------------------------------------------------------------------
*  为什么用频数表？因为 SPSS 的 Kappa 需要方阵，而频数表已把 M01–M10+OTHER 的
*  全部 121 个组合显式列出（含 0 单元），并把 (OTHER, OTHER) 这一格预置了
*  0.0001 的极小权重 —— 这样 OTHER 在行、列两侧都会出现，表格成为方阵，
*  而 Kappa 只从 0.85774059 变为 0.85774171（第 5 位小数起，可忽略）。
* #############################################################################.

GET FILE = f02.
DATASET NAME 频数表 WINDOW = FRONT.
DATASET ACTIVATE 频数表.

WEIGHT BY W_forKappa.

CROSSTABS
  /TABLES = A_Code BY B_Code
  /FORMAT = AVALUE TABLES
  /STATISTICS = KAPPA
  /CELLS = COUNT ROW COLUMN TOTAL
  /COUNT ROUND CELL.

*  输出中读什么：
*    Symmetric Measures 表 →  Kappa = .858 ；Asymp. Std. Error = .092 ；
*                             Approx. T ≈ 9.3 ；Approx. Sig. < .001 ；N of Valid Cases = 17
*    Crosstabulation 表    →  行 = AI 标注语步，列 = 标准语步；对角线为一致单元数
*                             （非对角线唯一有值的两个单元：
*                                行 M06   × 列 M07 = 1
*                                行 OTHER × 列 M01 = 1    ← 即两处分歧）。

WEIGHT OFF.


* #############################################################################
*  路线 B：每单元一行的原始长数据  →  同样的整体 Kappa（交叉验证 / 做其它分析用）
* -----------------------------------------------------------------------------
*  原始 17 行里 OTHER 只出现在 A 侧，直接用会非方阵；这里用 SPSS 语法
*  追加 1 个"虚拟个案"（A=11, B=11, 权重 0.0001）来补齐（UCLA / IBM 社区标准做法）。
* #############################################################################.

GET FILE = f01.
DATASET NAME 主数据 WINDOW = FRONT.
DATASET ACTIVATE 主数据.

COMPUTE w = 1.
EXECUTE.

DATA LIST FREE / RaterA_Outer_Code RaterB_Code w.
BEGIN DATA.
11 11 0.0001
END DATA.
DATASET NAME 补齐行.

DATASET ACTIVATE 主数据.
ADD FILES /FILE = *
  /FILE = 补齐行.
EXECUTE.
DATASET CLOSE 补齐行.

WEIGHT BY w.

CROSSTABS
  /TABLES = RaterA_Outer_Code BY RaterB_Code
  /FORMAT = AVALUE TABLES
  /STATISTICS = KAPPA
  /CELLS = COUNT
  /COUNT ROUND CELL.

WEIGHT OFF.

*  ---- 附加：描述统计与一致率（在"主数据"集上，不加权） ----.
FREQUENCIES VARIABLES = RaterA_Outer RaterB_Standard RaterA_Inner
  /ORDER = ANALYSIS.

FREQUENCIES VARIABLES = Agree_Strict Agree_Lenient
  /STATISTICS = MEAN SUM
  /ORDER = ANALYSIS.
*    Agree_Strict  均值 = .8824  → 严格一致率 88.24%（15/17）
*    Agree_Lenient 均值 = .9412  → 宽松一致率 94.12%（16/17；标准语步命中 A 的
*                                  {外层, 内层} 集合即算一致）。

CROSSTABS
  /TABLES = RaterA_Outer BY RaterA_Inner
  /FORMAT = AVALUE TABLES
  /CELLS = COUNT
  /COUNT ROUND CELL.
*    → 查看 AI 嵌套标注的"外层 × 内层"分布（本例 10/17 个单元带子语步）。


* #############################################################################
*  路线 C：逐语步 Kappa（把每个语步拆成 2×2 表：该语步 是 / 否）
* -----------------------------------------------------------------------------
*  用途：定位"到底是哪几个语步最容易混淆"。整体 Kappa 高并不代表每个语步都好。
*  本例预期：M02 / M05 / M08 = 1.000 ；M06 = .821 ；M07 = .821 ；
*            M01 = .638 ；OTHER = .000（B 侧从未使用）
* #############################################################################.

GET FILE = f03.
DATASET NAME 二分长表 WINDOW = FRONT.
DATASET ACTIVATE 二分长表.

WEIGHT BY W_forKappa.

*  剔除双方都从未使用的语步（M03 / M04 / M09 / M10）：它们的 2×2 表退化为
*  一行一列，Kappa 在数学上恒为 0，没有信息量。
*  若你想看它们（会得到 ≈ 0），把下面三行注释掉即可。
USE ALL.
COMPUTE filter_$ = (MoveCat ~= 'M03' & MoveCat ~= 'M04' & MoveCat ~= 'M09' & MoveCat ~= 'M10').
FILTER BY filter_$.
EXECUTE.

SORT CASES BY MoveCat.
SPLIT FILE SEPARATE BY MoveCat.

CROSSTABS
  /TABLES = A_Flag_Outer BY B_Flag
  /FORMAT = AVALUE TABLES
  /STATISTICS = KAPPA
  /CELLS = COUNT ROW COLUMN TOTAL
  /COUNT ROUND CELL.

SPLIT FILE OFF.
FILTER OFF.
USE ALL.
WEIGHT OFF.


* #############################################################################
*  路线 D（可选）：加权 Kappa —— 序数敏感性分析
* -----------------------------------------------------------------------------
*  谨慎使用：语步 M01–M10 在本编码体系中本质上是【名义变量】，
*    "M01 与 M02 的距离"和"M01 与 M08 的距离"没有可解释的序数含义。
*    加权 Kappa 仅在审稿人 / 导师坚持要求时作为补充报告即可。
*    另注意：SPSS 会把 OTHER 当作与 M10 相邻的类别（距离 1/10），
*    会与"OTHER 与任何语步都算完全不一致"的算法结果不同。
*    参考值（按 OTHER = 与任何语步完全不一致计算）：线性 .794 / 二次 .676。
* #############################################################################.

* GET FILE = f02.
* WEIGHT BY W_forKappa.
* CROSSTABS
*   /TABLES = A_Code BY B_Code
*   /FORMAT = AVALUE TABLES
*   /STATISTICS = KAPPA(1) KAPPA(2)      /* (1)=线性权重 (2)=二次权重；旧版本若报错，只留 KAPPA */.
*   /CELLS = COUNT
*   /COUNT ROUND CELL.
* WEIGHT OFF.


* =============================================================================
*  附：完全用菜单（不写代码）的操作路径
* =============================================================================
*  整体 Kappa：
*    1. 打开 SPSS_02_频数加权表_AxB.sav
*    2. 数据(D) → 加权个案(Weight Cases) → 加权个案依据 → 选 W_forKappa → 确定
*    3. 分析(A) → 描述统计 → 交叉表(Crosstabs)
*         行(Row)    = A_Code
*         列(Column) = B_Code
*    4. 点"统计(Statistics)" → 勾选 Kappa → 继续
*    5. 点"单元格(Cells)"    → 勾选 观察值 / 行 / 列 / 总计 → 继续 → 确定
*    6. 输出窗口找 "对称度量(Symmetric Measures)" 表，读 Kappa 那一行
*
*  逐语步 Kappa：
*    1. 打开 SPSS_03_逐语步二分长表.sav
*    2. 数据 → 加权个案 → W_forKappa
*    3. 数据 → 拆分文件(Split File) → 比较组 → 分组依据 = MoveCat → 确定
*    4. 分析 → 描述统计 → 交叉表：行 = A_Flag_Outer，列 = B_Flag → 统计 → Kappa
*        （若要剔除 M03/M04/M09/M10：数据 → 选择个案 → 如果条件满足 →
*          MoveCat ~= 'M03' & MoveCat ~= 'M04' & MoveCat ~= 'M09' & MoveCat ~= 'M10'）
*
*  注意：SPSS 的 CROSSTABS 不提供 Kappa 的 Bootstrap 置信区间。
*       论文里若需 CI，请用本目录下 SPSS_04_Kappa结果汇总.csv 中
*       由 Python 给出的 95%CI（正态近似 [.6765, 1.000]；Bootstrap [.6458, 1.000]）。
* =============================================================================.
