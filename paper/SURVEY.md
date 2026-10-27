# SURVEY — 文献核实与贡献定位（SPEC 第 3 节，W0.2 闸门文档）

> 生成日期：2026-10-28。本文件只引用 `refs.bib`（由 `fetch_refs.py` 从 arXiv API 生成）中的论文，
> 每处引用标注 bibtex key 与 arXiv id，可逐一 grep 验证。
> 无 arXiv 版的库外候选论文的核查记录在 `PROGRESS.md`，按 SPEC 6.2 不在本文件提名。

## 0. 检索与阅读方法

- 五个规定检索式（arXiv Atom API，relevance 排序，每方向读取前 25 条结果、保留相关者 ≤8 篇入库）：
  1. `all:"dueling bandits"`；2. `all:"top-k" AND all:"pairwise comparisons"`；
  3. `all:"Bradley-Terry" AND all:"sample complexity"`；4. `all:"ranking from pairwise comparisons"`；
  5. `all:"graph" AND all:"bandit" AND all:"sample complexity"`。
- 18 条窄化种子标题检索补齐关键论文（如 `ti:"Spectral MLE"`、`ti:"sharp minimax bounds"`、
  `ti:"Bradley-Terry model under general comparison graphs"` 等）。
- 闸门专项"猎杀式"补查（专门找可能覆盖本设定的论文，全部执行于 2026-10-28）：
  `comparison graph+identification`、`dueling+graph constraints`、`algebraic connectivity+ranking`、
  `restricted comparisons+sample complexity`、`top-k+comparison graph`、`graph-restricted+bandit`、
  `general comparison graphs`、`partial comparison graph`、`restricted comparisons+ranking`，
  以及 Web 搜索引擎交叉验证（命中候选逐篇打开原文核查）。
- 入库 35 篇，**35 篇摘要全部通读**（`refs_raw.json` 为证），其中 10 篇设定最近的文章逐句精读。

## 1. 已有工作样本复杂度界清单

记号：n 物品、gap Δ=θ_(k)−θ_(k+1)、置信 δ、比较图 G、λ_G 为图 Laplacian 代数连通度。
"全访问"= 算法可任选一对物品比较；"随机图设计"= 观测到哪些对由随机采样决定、算法不能重复或自适应选边；
"固定受限图"= 算法只能反复比较**给定**图 G 的边（本 SPEC 的设定）。

### 1a. 全访问（或被动随机设计）下的 top-k 识别

| 文献 | Setting | 上界 | 下界 |
|---|---|---|---|
| shah2015simple (1512.08949) | 被动、每对至多一次，Borda/Copeland 计数，无参数假设 | top-k 恢复，达信息论极限（常数因子内最优） | 隐含（最优性声明含匹配下界论证） |
| chen2015spectral (1504.07218) | BTL，随机非自适应采样 | spectral MLE 恢复 top-K | 给出可识别性的极小化必要条件（分离度 Δ） |
| heckel2016active (1606.08842) | 主动、非参数 Borda 分数、top-k 特例 | 计数算法，对数因子内最优 | — |
| heckel2018approximate (1801.01253) | 主动、(ε,δ) 近似 top-k | 置信区间计数算法，接近最优（对数因子内） | — |
| chen2017a (1707.08238) | 主动、多选一 MNL 模型 | 近 instance-optimal 算法 | 匹配下界（即使告知真实分数） |
| chen2017spectral (1707.09971) | BTL、**随机采样设计**、精确 top-K、固定 dynamic range | spectral / 正则 MLE 均极小化最优 | 极小化下界（随机设计） |
| goldberger2026optimal (2607.08979) | **全访问**、固定置信、BT 效用模型 | 渐近最优算法（对齐信息论下界的在线分配） | 信息论下界（对偶/saddle-point 结构） |
| chen2021optimal (2101.08421) | BTL 全排序（Kendall tau 极小化极大） | 分治+局部 MLE，达极小化极大率 | 极小化极大下界 |
| wang2022noisy (2202.01446) | 噪声排序（常数错误率、全访问） | 排序容量的上界 | 排序容量下界 |

**小结 a**：全访问 top-k 识别的样本复杂度已从常数级（shah2015simple、heckel2018approximate）推进到渐近最优
（goldberger2026optimal，2026）。**这一块问题已做透，本论文不得在此处声称任何"首次"。**

### 1b. BT 估计在一般/固定比较图上（λ_G 依赖已被确立的领域）

| 文献 | Setting | 上界 | 下界 |
|---|---|---|---|
| shah2015estimation (1505.01462) | BTL/Thurstone 估计 w*，误差界依赖比较图 Laplacian 谱 | 极小化极大紧上界 | 极小化极大紧下界（拓扑依赖） |
| li2021ellinftybounds (2110.10825) | BTL MLE 的 ℓ∞ 误差，一般比较图 | 依赖代数连通度 λ2 的 ℓ∞ 上界 | 充分正则图族上近似匹配的 ℓ∞ 极小化下界 |
| chen2023ranking (2304.06821) | BTL 分数估计，一般图（有效电阻刻画）+ 局部图 | MLE 达 Cramér-Rao（逐条目、有效电阻形式） | Cramér-Rao 论证 |
| yang2026graphmonotone (2610.09030) | **任意固定**比较图、BTL，MLE 与 Rank Centrality | 逐条目误差 O(1/√λ_D)（计数加权图代数连通度），graph-monotone | — |
| han2026bradleyterry (2610.06237) | 一般确定性比较设计、MLE 一致性与渐近正态 | 有效电阻 + Laplacian 谱隙的全局项 | 渐近正态下的 Cramér-Rao |
| negahban2012rank (1209.1688) | 随机图上的随机游走排序（估计） | Rank Centrality 误差界 | — |
| osting2012optimal (1207.6430) | 比较图**实验设计**：Fisher 信息最大化 | 数据收集问题归约为"找代数连通度大的图" | — |

**小结 b**：**估计问题**上，"1/λ_G（或有效电阻）控制信息在比较图上的传播"已是确立事实，
且上下界齐备（shah2015estimation、li2021ellinftybounds）。本论文若声称"首次发现比较图连通度影响统计难度"即为造假；
只能声称：把这一依赖**迁移到 top-k 识别样本复杂度**（带 Δ、k、δ 的决策型问题）并给出识别特有的下界。

### 1c. 图受限/半随机设计下的 top-k 识别（与本设定最接近的邻居）

| 文献 | Setting | 上界 | 下界 |
|---|---|---|---|
| yang2024topk (2402.07445) | top-K，**半随机**比较图（随机图 + 单调对手加边），加权 MLE | 近最优样本复杂度（差 log²(n)），ℓ∞ 误差 ↔ 加权图谱性质 | — |
| heckel2018approximate / 1a 各篇 | 随机/全访问 | 见 1a | 见 1a |
| russo2025pure (2503.07824) | **反馈图**纯探索（BAI，观察邻域奖励，非成对比较） | 渐近最优 TaS-FG | 实例特定下界 |
| cohen2016online (1605.07018) | 反馈图遗憾最小化（图甚至不揭示） | 随机情形 Θ̃(√(αT)) | 对抗情形不可改善 |
| sentenac2021pure (2108.00230) | matching bandits（结构化纯探索） | rank-1 假设降低样本复杂度 | — |

**小结 c**：图约束纯探索存在于两个**不同模型**——反馈图（russo2025pure、cohen2016online，单臂拉动+邻域观察）
与奖励平滑图（见 1d 谱带臂）。成对比较模型中，图约束识别只有半随机图上的上界（yang2024topk）。
**没有一篇给出"给定固定图 G 上、只能比较 G 的边、以 λ_G 表出的 top-k 识别上下界"。**

### 1d. dueling bandits 与偏好 bandit

| 文献 | Setting | 结果类型 |
|---|---|---|
| zoghi2013relative (1312.3393) | K 臂 dueling，RUCB，Condorcet winner | 遗憾 O(log t) |
| agrawal2019klucb (1902.02778) | Copeland dueling | 遗憾界 |
| bengs2023identifying (2310.00750) | 三元反馈 Copeland winner 识别（全访问） | 样本复杂度下界 + 近匹配算法 POCOWISTA |
| wu2023borda (2303.08816) | 广义线性 dueling，Borda 遗憾 | 下界 Ω(d^{2/3}T^{2/3}) + 近匹配 |
| li2024feelgood (2404.06013) | 情境 dueling | 近极小化极大遗憾 |
| deb2026replicable (2610.20908) | 可复制性约束 dueling | 次线性遗憾 |
| sharma2026lipschitz (2604.00523) | 连续动作空间 Lipschitz dueling | 遗憾 T^{(d_z+1)/(d_z+2)} |
| yahmed2026on (2609.39351) | 一般函数类偏好 bandit（BT 反馈） | eluder 维度复杂度刻画（遗憾） |
| jamieson2011active (1109.3701) | 欧氏嵌入下的主动排序 | d·log n 量级比较次数 |
| saha2021dueling (2107.02274) | 对抗休眠 dueling | 实例特定遗憾下界 |

**小结 d**：dueling bandits 主线是**遗憾**，识别型（pure exploration）结果只覆盖 winner/Copeland 且全访问
（bengs2023identifying），同样没有图受限变体。

## 2. 与 SPEC 第 2 节初稿贡献的逐条对照

| SPEC 初稿贡献 | 最近已有工作 | 差异 | 必须修订的表述 |
|---|---|---|---|
| 1. 下界 T ≥ Ω((n/Δ²)·log(1/δ)·(1/λ_G) + (n/Δ)·k)，固定受限图 | goldberger2026optimal（全访问信息论下界）；shah2015estimation、li2021ellinftybounds（估计下界含 λ2/拓扑）；chen2017spectral（随机设计 top-K 下界） | 无人给出"固定图 G 上识别型"下界；估计型下界证明的是估计误差而非识别样本数 | 不声称下界技术"首次"以外的任何既有结论；证明须显式说明与估计型拓扑下界的联系（复用其 λ2 障碍手法）与差异（识别只差 Top-k 边界处的 Δ，需 (n/Δ)·k 型论证） |
| 2. 上界：图上随机游走 successive elimination，T ≤ O((n/Δ²)·log(n/δ)·(1/λ_G) + (n/Δ)·k·log n) | yang2024topk（半随机图 top-K 上界）；yang2026graphmonotone、han2026bradleyterry（固定图 MLE 逐条目误差 1/√λ_D 型） | 无人写出固定图上"逐边重复比较 + 淘汰"的显式 T(n,k,Δ,G,δ) 定理；上界可由估计界+阈值化拼出，故贡献在于显式化与算法（随机游走采样均衡） | 用 "To the best of our knowledge"；明写"上界可视为固定图估计界（yang2026graphmonotone）向识别问题的转述 + log 因子代价"，贡献重点放在**下界匹配到 log 因子** |
| 3. 完全图退化 O(n/Δ²·log(1/δ)) 对齐已知结果 | shah2015simple、heckel2018approximate、goldberger2026optimal | 这正是自检点，成立且必须引用对齐 | 命题 4.3 的作用改为"与 1a 中紧界一致性校验"，引用三篇对齐 |
| 4. 实验验证 T 随 1/λ_G 缩放 | shah2015estimation、li2021ellinftybounds（估计误差 vs 拓扑的仿真）；osting2012optimal（设计视角） | 识别样本数 vs λ_G 的实测无人做过 | 实验动机段引用 osting2012optimal 说明"实验设计早已指出代数连通度是核心量" |

## 3. 诚实结论（三选一）

> **结论：选择第三条——"确实空着"，保持 SPEC 第 2 节原定位**，但附带下列强制修订（详见第 2 节表末列）。

**为什么不选第一条（已被紧界覆盖 → 改定位）**：
本设定的核心要素是"**给定**固定图 G、算法只能比较 G 的边（可重复、可自适应）、δ-正确 top-k 识别、
以 λ_G 与 Δ 表出的 T(n,k,Δ,G,δ)"。猎杀式检索与 35 篇全读均未发现任何工作给出该设定的上下界：
全访问已被做透（goldberger2026optimal），随机图设计已被做透（chen2017spectral、chen2015spectral），
半随机图只有上界（yang2024topk），固定图上只有**估计**（非识别）的 λ_G 型界
（shah2015estimation、li2021ellinftybounds、yang2026graphmonotone、han2026bradleyterry、chen2023ranking）。

**为什么不选第二条（只有上界没有下界 → 改为补下界）**：
固定受限图上连显式的识别型**上界**也没有（最接近的是半随机图 yang2024topk 与可由
yang2026graphmonotone 估计界间接拼出的隐式上界）。"补下界"定位会让论文放弃上界与算法部分，
而这部分（把固定图估计界显式化为识别定理 + 图游走采样算法）恰好是文献空白的一半，没有理由放弃。

**为什么可以选第三条（保持原定位）**：
识别型问题（决策、Δ 间隔、k、δ）在固定受限图上的样本复杂度刻画，在本次核实范围内是空白；
且初稿上下界的形式（1/λ_G 项 + (n/Δ)·k 项）与估计文献的 λ2 障碍不矛盾，完全图退化与 1a 紧界一致。

**必须执行的诚实性修订（Wave 1/2 写作时强制）**：
1. 全文禁止声称 top-k 识别、下界方法、完全图情形的任何"首次"；一律 "To the best of our knowledge，
   no existing work gives … for a fixed restricted comparison graph"，并与 1a/1b/1c 三块逐一对照。
2. 摘要与引言必须写明：λ_G 控制比较图信息传播在**估计**理论中已确立（引 shah2015estimation、
   yang2026graphmonotone、li2021ellinftybounds）；本文贡献是把它带进**识别**样本复杂度并补识别特有的下界。
3. 完全图退化命题（4.3）引用 shah2015simple、heckel2018approximate、goldberger2026optimal 作对齐。
4. Related Work 必须包含：1a ≥4 篇、1b ≥4 篇、1c ≥2 篇、1d ≥3 篇（均已在 refs.bib）。
5. 定理 4.1 若证明受阻，按 SPEC 第 4 节规则降级 Conjecture，不得含糊。

**风险登记**：本次核实的盲区是"无 arXiv 版本的会议论文"与"2026 年 10 月后新预印本"。
库外候选已核查四篇（记录见 PROGRESS.md），均不覆盖固定图识别设定；正式写作前（Wave 1 开工时）建议重跑一次
`fetch_refs.py` + 猎杀式检索以刷新。
