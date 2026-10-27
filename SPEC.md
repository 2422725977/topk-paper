# 规格书：论文《Top-k Identification from Noisy Pairwise Comparisons under Restricted Comparison Graphs》

> 交付对象：实现该任务的 AI Agent。本文件是唯一需求来源。
> **第 1 波不是写代码，是文献核实。跳过它直接写论文，整篇作废。**

## 0. 一句话定位

We study how restricting which pairs can be compared changes the sample complexity of identifying the top-k items under a Bradley-Terry model, and give matching upper and lower bounds in terms of the comparison graph's connectivity and the separation gap.

## 1. 问题形式化（LaTeX 第 3 节照此展开）

**对象与实力**：`[n] = {1,...,n}`，每个对象 i 有未知实力 `θ_i ∈ ℝ`。

**可比较图**：无向图 `G = ([n], E)`，只有当 `{i,j} ∈ E` 时才能比较 i 与 j。`Δ_G` 记图直径，`λ_G` 记图 Laplacian 的次小特征值（代数连通度）。

**比较模型（Bradley-Terry）**：比较 `{i,j}` 的结果 `Y ∈ {i,j}`，满足
```
P(Y = i) = σ(θ_i - θ_j) = 1 / (1 + exp(-(θ_i - θ_j)))
```

**间隔**：设排序 `θ_(1) ≥ θ_(2) ≥ ... ≥ θ_(n)`，定义 Top-k 分界间隔
```
Δ = θ_(k) - θ_(k+1)
```

**目标**：算法只能用 G 上的边做比较，输出 `Ŝ ⊂ [n]`，`|Ŝ| = k`，使得
```
P(Ŝ = { (1),...,(k) }) ≥ 1 - δ
```
记所需最少比较次数为 `T*(n, k, Δ, G, δ)`。

## 2. 贡献定位（初稿，Wave 0 核实后必须修订）

1. **下界**：在受限比较图上，任何 δ-正确的算法需要
   ```
   T ≥ Ω( (n/Δ²) · log(1/δ) · (1/λ_G) + (n/Δ) · k )
   ```
   直觉：`1/λ_G` 项来自信息在图上的传播速度——比较图越"细长"，把全序信息传递开需要的比较越多；`(n/Δ)·k` 项来自区分 Top-k 与第 k+1 名需要的最少重复次数。

2. **上界**：给出一个基于「图上随机游走顺序的 successive elimination」算法，达到
   ```
   T ≤ O( (n/Δ²) · log(n/δ) · (1/λ_G) + (n/Δ) · k · log n )
   ```
   与下界相差 log 因子。

3. **完全图退化**：当 G 是完全图时，λ_G = n，上下界退化为已知的 `O(n/Δ² · log(1/δ))`，与现有工作一致——**这是正确性的自检点，必须写进论文**，证明这套界没有凭空捏造。

4. **实验**：在随机图 / 环形图 / 星形图 / 带瓶颈的图上验证 `T` 随 `1/λ_G` 的真实缩放。

## 3. 第 0 波：文献核实（最重要，必须先做）

用 arXiv API + Semantic Scholar，检索下列方向，每方向至少读 8 篇摘要：

| 检索式 | 要回答的问题 |
|---|---|
| `all:"dueling bandits"` | Top-k / best-arm identification 已有的样本复杂度界是什么 |
| `all:"top-k identification" AND all:"pairwise comparison"` | 是否已有人做 Top-k 的下界 |
| `all:"Bradley-Terry" AND all:"sample complexity"` | BT 模型下的紧界到哪一步 |
| `all:"ranking from pairwise comparisons"` | 比较图受限的变体是否已被研究 |
| `all:"graph" AND all:"bandit" AND all:"sample complexity"` | 图约束 bandit 的现有结果 |

**产出 `paper/SURVEY.md`**：

1. 已有工作的样本复杂度界清单（谁、什么 Setting、上界、下界）
2. **你的贡献与它们的差异**，逐条对照
3. **诚实结论三选一**：
   - 若发现已有紧界覆盖你的设定 → **改定位**：把贡献改为「特定图族（如环形/星形）下的精确常数」或「有限预算下的自适应停止规则」
   - 若发现只有上界没有下界 → 贡献改为「补下界」
   - 若确实空着 → 保持第 2 节原定位

**这一节的结论必须写进 PROGRESS.md，不许跳过。** 如果核实后发现整个题目已被做透，就明写「该方向已被 X 篇工作覆盖，建议换题」，然后停下——**不许为了产出而硬写一篇重复劳动的论文**。

## 4. 要证的定理

**定理 4.1（下界）** 见第 2 节第 1 条。
证明骨架：构造两个"难分辨"的参数实例 θ 与 θ'，它们只在 Top-k 边界附近差 Δ；用 KL 散度量化单次比较能提供的区分信息最多 `O(Δ² / d_G(i,j))`（d_G 为图上距离）；再对图上所有比较做信息累积，用 Le Cam 两点法得到总 KL 上界，最后由 Pinsker 不等式得到 δ 下界。**关键在于 `1/λ_G` 如何从"图上距离的期望"导出**，这一步要写清推导。

**定理 4.2（上界）** 见第 2 节第 2 条。
证明骨架：在图上做随机游走采样边，每个对象获得样本量近似均衡；用 Hoeffding 构造每对 (i,j) 的 θ_i - θ_j 置信区间；再做 successive elimination 逐轮淘汰。`λ_G` 通过随机游走的混合时间进入界。

**命题 4.3（完全图退化）** 令 G = K_n，则 4.1 与 4.2 退化为经典结果。这是自检，必须写。

**证明写不出来时的规则**：降级为 Conjecture，并在正文明确写 `We conjecture ... (proof incomplete)`。**禁止假装证完。**

## 5. 实验设计（`paper/code/`）

| 实验 | 设置 | 产出 |
|---|---|---|
| E1 完全图 | n ∈ {10,20,50}, Δ ∈ {0.2,0.5,1.0}, δ=0.05 | 实测 T 与 `n/Δ²` 是否成正比 |
| E2 图上缩放 | 随机图 / 环形 / 星形 / 哑铃图，n=50，同 Δ | 实测 T 与 `1/λ_G` 的关系 |
| E3 间隔依赖 | 固定 n, G，扫 Δ ∈ [0.1, 1.5] | T 随 Δ 的斜率是否为 -2 |
| E4 预算受限 | 固定预算 B < T*，测错误率 | 错误率随 B 的曲线 |
| E5 对比基线 | 均匀采样 + 多数投票 vs 你的算法 | 同错误率下所需比较次数的比值 |

每个实验 **至少 100 次重复**（E5 至少 50 次），报告均值与 95% 置信区间。结果写 `paper/results/*.json`。

**图参数必须实测**：`λ_G` 用 numpy 算 Laplacian 特征值，不许用近似公式。

## 6. 反伪造

1. 论文里每个数字必须能在 `paper/results/*.json` 里 grep 到 → 写 `check_paper.py` 自动核验，不通过则非零退出。
2. BibTeX 只能由 `fetch_refs.py` 从 API 生成，禁止手写。`SURVEY.md` 里提到的每篇论文都必须出现在 `refs.bib` 里。
3. 定理证不完就标 Conjecture，不许含糊。
4. 实验次数不许虚报：跑了 87 次就写 87，不许四舍五入成 100。

## 7. 论文结构（`paper/main.tex`，英文）

`article` 类，宏包 `amsmath, amsthm, booktabs, hyperref, algorithm, algpseudocode, tikz`（本机 TinyTeX 已装齐，缺什么用 `tlmgr install` 补并记录）。

| 节 | 内容 | 篇幅 |
|---|---|---|
| Abstract | 问题 + 受限图 + 上下界 + 完全图退化 | 150 词 |
| 1 Introduction | 现实动机（模型对战只能比同尺寸、评测预算有限）+ 贡献列表 | 0.75 页 |
| 2 Related Work | dueling bandits、best-arm identification、BT 估计、图约束 bandit | 1 页 |
| 3 Problem Setup | 第 1 节全部定义 | 1 页 |
| 4 Lower Bound | 定理 4.1 完整证明 | 1.5 页 |
| 5 Algorithm & Upper Bound | 算法伪码 + 定理 4.2 证明 | 1.5 页 |
| 6 Experiments | E1–E5，booktabs 表格 + matplotlib 存 PDF 的图 | 2 页 |
| 7 Discussion | 局限：BT 假设、静态 θ、无预算自适应 | 0.5 页 |
| 8 Conclusion | | 0.25 页 |
| References | 20–35 条真引用 | — |

总长 9–12 页。编译：`latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex`，`main.log` 里 Reference/Citation 未定义警告必须为 0。

## 8. 中文导读（`paper/zh-guide.md`，必须有）

他看不懂英文论文。每节一段中文，100–200 字，必须回答三件事：

```
## 4 Lower Bound（下界）
**这节在说什么**：……
**为什么这么证**：为什么会想到用 KL 散度，而不是直接数次数……
**你需要能回答**：为什么比较图越细长，需要的比较次数越多？
```

覆盖全部 8 节 + 三个定理 + 每条公式的直觉。**不许写"如上所述"，不许把英文翻译一遍了事**，要讲人话。

## 9. 分波任务

### Wave 0（今晚，5–6 小时）

| # | 任务 | 产出 | 验收 |
|---|---|---|---|
| W0.1 | `paper/fetch_refs.py`：按第 3 节五个方向抓 25–35 篇真论文，生成 `refs.bib` | bib | `grep -c '@'` ≥ 25，每条有真实 arxiv_id |
| W0.2 | **`paper/SURVEY.md`：文献核实 + 贡献定位结论** | md | 每条已有工作写出上界/下界；结论从第 3 节的三选一中明确选一 |
| W0.3 | `paper/code/simulate.py`：BT 采样器 + 图生成器（完全图/随机/环/星/哑铃）+ `λ_G` 实测 | py | 五种图的 λ_G 数值打印出来，完全图 ≈ n |
| W0.4 | `paper/code/algorithms.py`：`uniform_majority`、`successive_elimination`、`graph_walk_elimination`（你的算法） | py | `test_algorithms.py` 在 n=5、Δ=2 的易例上三个算法都 100% 正确 |
| W0.5 | 跑 E1 + E3 | `results/e1.json`, `e3.json` | 每个配置 ≥100 次重复；E3 拟合出的 Δ 斜率写进 PROGRESS |
| W0.6 | `paper/check_paper.py` 数字核验脚本 | py | 植入假数字能检出（自测写进 PROGRESS） |

**W0.2 是闸门**：如果 SURVEY 结论是"已被做透"，停下来报告，不要继续 W0.3–W0.6。

### Wave 1（第二晚）
- W1.1 定理 4.1 完整证明写进 tex 第 4 节。
- W1.2 算法 + 定理 4.2 证明写进第 5 节。
- W1.3 跑 E2、E4、E5。
- W1.4 编译通过，页数 ≥ 7。

### Wave 2（第三晚）
- W2.1 写第 1、2、6、7、8 节正文 + 实验图表。
- W2.2 命题 4.3（完全图退化）写清楚并数值验证。
- W2.3 `check_paper.py` 全过，编译零未定义引用。
- W2.4 写 `zh-guide.md` 中文导读。
- W2.5 最终 PDF。

## 10. 全局约束

- 工作目录 `/Users/xi/Documents/topk-paper/`（**独立仓库，与 exam-diag 完全无关，不许碰 exam-diag 任何文件**）
- 每步 `git commit` + `git push`（SSH remote 已配通）
- 依赖只允许：numpy、matplotlib、pytest、scipy
- 作者：`Xin Xia`，单位 `Chongqing Technology and Business University`
- 不投稿、不发邮件。产出是 preprint 草稿。
- **不声称"首次提出"**：除非 SURVEY 核实确认，否则一律用 `To the best of our knowledge` 并给出对照。

## 11. 完成后报告

1. PDF 路径与页数
2. SURVEY 的结论选了哪一条、依据是哪几篇
3. 三个定理各是否证完
4. E1–E5 各跑多少次、关键数字
5. check_paper.py 结果
6. 哪些引用抓不到
