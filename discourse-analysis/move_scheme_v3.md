# 进一步精简版语步方案（v3）：大学外语院系 About Us 文本

> 参考：Yu (2023) 对领导致辞体裁采用 **10 个 Move** 的方案；Yu et al. (2026) 的 6 Move 方案（BACKGROUND/PURPOSE/METHOD/RESULTS/CONCLUSION/OTHER）及 combined moves、OTHER 过滤、双模型一致性校验方法。  
> 目标：在 v2（13 Moves）基础上进一步精简为 **10 Moves + OTHER**，与 Yu (2023) 的 Move 数量对齐，降低标注负担。  
> 适用文本：中国与美国大学外语院系官方网站 About Us / 简介页面。标注粒度：句子级。

## 一、v2 → v3 精简对照

| v3 编号 | v3 Move 名称 | 合并来源（v2） | 合并理由（参考 Yu） |
|---|---|---|---|
| M01 | 机构定位与组织架构 | v2 M01 | 保留（Yu 2023 也保留机构定位类 Move） |
| M02 | 历史沿革与学脉传承 | v2 M02 | 保留 |
| M03 | 价值准则、学科内涵与社会服务 | v2 M03 | 保留（Yu 2023 将"使命/价值观"合并为 fewer moves） |
| M04 | 学位项目与课程供给 | v2 M04 | 保留 |
| M05 | 育人目标、教学模式与毕业出路 | v2 M05 + v2 M10 | 将"在读培养"与"毕业去向"合并为"教育全程" Move，减少 Move 数；职业导向表述仍可在此 Move 中识别（Yu 2023 以 communicative purpose 为准则，不按时间切分） |
| M06 | 研究议程与学术专长 | v2 M06 | 保留 |
| M07 | 师资力量与支撑资源 | v2 M07 | 保留 |
| M08 | 学术声誉与办学成就 | v2 M08 | 保留（含 dated news） |
| M09 | 合作网络与国际交流 | v2 M09 | 保留 |
| M10 | 未来愿景、欢迎与联系信息 | v2 M11 + v2 M12 | 将未来取向与读者接触合并为"收尾/面向未来" Move（Yu 2023 将欢迎读者与未来规划视为同一收尾功能） |
| OTHER | 非简介话语残渣 | v2 OTHER + v2 M13 | 将 v2 M13（规章/募捐/缅怀/动态）整体并入 OTHER，以子标签区分（Yu 2026 的 OTHER 标签吸收所有不匹配 Move） |

**精简效果**：v2 13 → v3 10（再减 23%）；相对原 19 减少 47%。

## 二、各 Move 定义与边界准则（精简版）

### M01 机构定位与组织架构
同 v2 M01。当前治理/结构 = M01；师资规模/设施 = M07；仅列中心名称 = M01；历史沿革 = M02；排名/荣誉 = M08；裸导航 = OTHER。

### M02 历史沿革与学脉传承
同 v2 M02。时间线过去 = M02；当前学位/课程 = M04；讣告 = OTHER（缅怀并入 OTHER）；历史种族主义/土地承认谴责 = M03。

### M03 价值准则、学科内涵与社会服务
同 v2 M03。抽象 ethos/价值观/学科正当化/社会服务 = M03；学生能力培养 = M05；课程列表 = M04；未来战略 = M10。

### M04 学位项目与课程供给
同 v2 M04。学位/课程清单 = M04；教学方法 = M05；规章/截止 = OTHER；外部培训/测试 = M03；学生名册 = OTHER。

### M05 育人目标、教学模式与毕业出路
- **核心问题**：院系培养什么样的人才/能力，通过何种教学实践；毕业生去向与职业发展如何？
- 包含：目标学生能力（批判性思维、跨文化能力、沟通能力、跨学科/创新素养）、课堂教法、体验式/课外学习、毕业前跨学科经历；毕业后的职业领域/行业（含 "prepare students for careers in..."、"graduates have become..."）、就业/深造率、校友网络规模、具名校友职业故事。
- 边界：在读发展与毕业去向均 = M05；校友终身收获的感言若强调"学院如何塑造我" = M05。

### M06 研究议程与学术专长
同 v2 M06。必须描述本院系研究议程；外部联盟范围 = M07；发表/基金/奖项 = M08；仅列中心名称 = M01。

### M07 师资力量与支撑资源
同 v2 M07。投入条件与可用支持/资助 = M07；奖项/排名/重点学科 = M08；规章/截止 = OTHER；募款 = OTHER。

### M08 学术声誉与办学成就
同 v2 M08。含 dated news（具体奖项/任命/出版）。无日期累积成就 = M08；未来愿景 = M10。

### M09 合作网络与国际交流
同 v2 M09。机构合作与留学/交换 = M09；学生在课内获得跨文化技能 = M05；单向社会服务 = M03。

### M10 未来愿景、欢迎与联系信息
- **核心问题**：展望未来，机构承诺哪些愿景/战略？文本如何问候/邀请读者？在哪里可以联系到机构？
- 包含：未来取向的机构承诺与战略规划（"Looking ahead...", "will continue to build..."）；直接问候/欢迎标题、温暖结语、读者导向行动提示（"We warmly invite you to explore...", "Learn more about...", "Please don't hesitate to get in touch..."）；办公室位置、地址、房间号、办公时间、电话/传真、邮箱、联系人卡片。
- 边界：募款呼吁 = OTHER；裸 "Contact Us" 标题 = OTHER；"look forward to welcoming you" = M10。

### OTHER 非简介话语残渣（扩展）
- (a) 导航菜单、无动词标题、HTML/alt 片段、乱码、采集者笔记；
- (b) 纯名录卡片、重复侧边栏/页脚；
- (c) 跑题文本、第三方组织自述；
- (d) **规章/程序/权责边界**（binding requirements, credit minimums, deadlines, disclaimers）；
- (e) **募款与捐赠者致谢**（donation calls, gift impact, donor acknowledgements）；
- (f) **讣告与缅怀**（obituaries, In Memoriam, tributes for deceased individuals）；
- (g) **具体 dated 新闻/活动**（dated lectures, seminars, workshops, recent awards/appointments/publications）——若与声誉成就强相关，可归 M08；否则归 OTHER。

> 注：(d)–(g) 在 v2 中为独立 Move（M13/M17/M18/M19），v3 为降低负担并入 OTHER，但建议在 OTHER 中用括号注明子类型，如 `<OTHER>(regulation) ...</OTHER>`，以便后续统计。若需保留其分析价值，可升级为独立 Move（回退至 v2）。

## 三、combined moves 规则

同 v2：双 Move 对等共现时嵌套 `<MXX><MYY>...</MYY></MXX>`；外层 = 主导 Move（信息量/篇幅更重），若难判断按编号升序；从属修饰语不单独成 Move。

## 四、格式规范

同 v2：一句一行、标签仅句首句尾、块级元素整块包裹、保留原文 100%、仅输出 XML 标注文本。

## 五、与 Yu (2023) / Yu et al. (2026) 的对应

- **Yu (2023)**：Move 识别基于"explicit metafunction"，句子级边界，10 个 Move；本 v3 亦为 10 个 Move，便于与已有研究的 Move 数量对齐与比较。
- **Yu et al. (2026)**：OTHER 标签吸收所有不匹配 Move；combined moves（如 PURPOSE+METHOD）；双模型 + 人工校对不一致项；报告 corrected accuracy 与 Cohen's κ；避免 positional bias 与 lexical trigger traps。本 v3 沿用这些方法论建议。

## 六、版本选择建议

- **需要精细分析规章/募捐/缅怀/新闻** → 使用 v2（13 Moves）。
- **以 RQ1–RQ5 为核心、降低标注负担** → 使用 v3（10 Moves），OTHER 中保留子类型注记以便后续筛选。
