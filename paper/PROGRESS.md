# PROGRESS — Top-k Identification under Restricted Comparison Graphs

> 反伪造三规则（SPEC 第 6 节，贯穿全程）：
> 1. 论文正文每个数字必须能在 `paper/results/*.json` 中 grep 到，由 `paper/check_paper.py` 自动核验，不通过非零退出。
> 2. `refs.bib` 只能由 `paper/fetch_refs.py` 从 arXiv/S2 API 真实返回生成，禁止手写；`SURVEY.md` 提到的每篇论文必须在 `refs.bib` 中。
> 3. 定理证不完就标 Conjecture；实验跑多少次写多少次，不许虚报。
>
> 闸门：W0.2 SURVEY 若结论为"该方向已被紧界覆盖"，写 `[STOP]` + 创建 `paper/STOP`，后续任务全部停做。

## W0.2 SURVEY（闸门）—— 结论已定，不触发 STOP

- **三选一结论：选第三条"确实空着"，保持 SPEC 第 2 节原定位**（附 5 条强制诚实性修订，见 `SURVEY.md` 第 3 节）。
- **判定不选第一条（未被紧界覆盖）的依据（全部在 refs.bib）**：
  - 全访问 top-k 已做透但设定不同：goldberger2026optimal (2607.08979，全访问渐近最优)、
    shah2015simple (1512.08949，常数最优)、heckel2018approximate (1801.01253，近似排序近最优)、
    chen2017a (1707.08238，MNL 匹配上下界)、chen2017spectral (1707.09971，随机设计极小化最优)。
  - 固定图上只有估计型 λ_G 界，无识别型：shah2015estimation (1505.01462)、li2021ellinftybounds (2110.10825)、
    yang2026graphmonotone (2610.09030，任意固定图 1/√λ_D)、han2026bradleyterry (2610.06237)、chen2023ranking (2304.06821)。
  - 图约束识别最近邻只有半随机图上界：yang2024topk (2402.07445)；反馈图纯探索模型不同：russo2025pure (2503.07824)、cohen2016online (1605.07018)。
  - 猎杀式检索 8 组查询（comparison graph+identification、dueling+graph constraints、restricted comparisons 等）均无命中。
- **库外候选核查日志**（无 arXiv 版、按 SPEC 6.2 不入 refs.bib，故 SURVEY.md 不提名；在此留档）：
  - Eriksson (AISTATS 2013) "Learning to Top-K Search using Pairwise Comparisons"：已下载原文（jmlr v31）通读前 3 页——比较**无噪声**（q=0）、观测对为 i.i.d. 随机子集、PATHRank 只保证 top-O(log N)，与 BT 噪声+固定受限图设定不符，不构成覆盖。
  - Agarwal, Khanna & Patil (AISTATS 2022) "PAC Top-k Identification under SST in Limited Rounds"：限制是轮数非比较图，不符。
  - Groves & Ben-Eliezer (EJOR 2019) "Top-κ selection with pairwise comparisons"：限制是总预算非比较图，不符。
  - Mohajer & Suh (ICML 2016) "A Sampling Lower Bound for Top-k Ranking"：全访问主动设计下界，非图受限；无 arXiv 版无法入库引用。
- **继续 W0.3–W0.6。**

## W0.1 refs（fetch_refs.py → refs.bib）

- 脚本：`paper/fetch_refs.py`（stdlib only，HTTP 走 curl——本机 anaconda Python 与 /etc/ssl/cert.pem 均缺 arxiv.org 使用的 Google "Certainly" 根证书，urllib SSL 验证失败，curl 走 macOS 信任库正常）。
- 数据源：arXiv Atom API（元数据+摘要）+ Semantic Scholar Graph API（citationCount，尽力而为）。
- **refs.bib 条目数：`grep -c '^@' paper/refs.bib` = 35**（目标 25–35 ✅）。
- 每方向保留（按 arXiv 相关度序、每方向上限 8、去噪后）：dueling_bandits 6、topk_pairwise 8、bt_sample_complexity 4、ranking_pairwise 7、graph_bandit 5（一篇论文可属多方向，种子论文 16 篇）。五个方向的查询与相关度排序均实际执行，摘要全部抓入 `refs_raw.json`。
- 全部 35 条均有真实 arxiv_id（由 arXiv API 在抓取时返回并验证，key 唯一）。
- S2 citationCount：ok=16 / fail=19（未认证接口限流，失败者保留 null，不影响条目真实性）。
- 抓不到的（已尝试、确认 arXiv 无对应条目，故不进 refs.bib，SURVEY 亦不提及）：
  - Mohajer & Suh 2016《A Sampling Lower Bound for Top-k Ranking from Pairwise Comparisons》（ICML 2016，无 arXiv 版）
  - Falahatgar et al.《Maxing and Ranking with Few Comparisons》（COLT 2018，无 arXiv 版）
  - Yue et al. 2012《The K-armed Dueling Bandits Problem》（JCSS 2012，无 arXiv 版）
  - Zoghi et al.《Dueling Bandits: Beyond Condorcet Winners》标题检索无 arXiv 条目
  - Feige et al. 1994《Computing with Noisy Information》（pre-arXiv）
  - 全文访问类经典（Mannor & Shamir 2011 侧观察）以 arXiv 版 1605.07018（Alon et al.）替代入库。
## W0.3 sim（simulate.py：BT 采样器 + 5 种图 + 实测 λ_G）

- 模块：`paper/code/simulate.py`（numpy eigvalsh 实测 Laplacian 次小特征值，无近似公式）。
- n=20 实测 λ_G（`python3 paper/code/simulate.py` 真实输出）：

| 图 | 边数 | λ_G 实测 | 理论对照 |
|---|---|---|---|
| complete | 190 | 20.000000 | = n ✓ |
| random (p=0.2, seed 0) | 36 | 0.471785 | np≈4 量级 ✓ |
| cycle | 20 | 0.097887 | 4π²/n² = 0.0987 ✓ |
| star | 19 | 1.000000 | 恰为 1 ✓ |
| dumbbell (2×10 团+桥) | 91 | 0.169048 | 瓶颈小 ✓ |

- BT 采样器 sanity：θ=[2,0] 时 10 万次比较经验胜率 0.8826 vs sigmoid(2)=0.8808 ✓。
## W0.4 algo（algorithms.py 三算法 + test_algorithms.py）

- 实现：`uniform_majority`（固定预算均匀采边+胜率投票，完全图等均衡图上有效）、
  `successive_elimination`（逐轮淘汰：每个活跃物品与均匀随机 G-邻居比较，预算逐轮加倍）、
  `graph_walk_elimination`（本文算法：每个活跃物品从自身出发做长度 c 的图上随机游走，途经边即比较）。
- 共享统计核：累计数据上的正则化 BT MLE（阻尼 Newton，gauge 用零均值钉住）+ 观测 Fisher 伪逆置信半径
  （曲率下限 1e-3 防可分离数据塌缩）+ 下界/上界逐轮淘汰。三个算法仅采样机制不同。
- 调试中修复的三个真实 bug（记录以供 Wave 1 引以为戒）：
  1. `_aggregate` 把同一无向边两个采样方向的"首端点胜场"混入同桶 → 标签翻转污染 MLE（改为按 (lo,hi) 规范方向计数）；
  2. BT 似然沿全 1 规范方向奇异，置信半径必须用 Moore-Penrose 伪逆（普通 +μI 会把 μ⁻¹ 漏进每个对角元，半径恒 ~1800）；
  3. 可分离（饱和）边上 MLE 发散 + 曲率→0 → 半径爆炸永不淘汰（曲率下限 + Newton 步长截断）。
- 验收（n=5、θ=[4,2,0,-2,-4] 即 Δ=2、完全图、k∈{1,2,3}，每配置 100 seeds）+ Δ=1 例（θ=[2,1,0,-1,-2]）：
  `pytest test_algorithms.py` → **7 passed in 3.50s**（含 cycle/star 稀疏图冒烟测试，均非 capped）。
- k=2、Δ=2、100 seeds 实测统计：三算法均 100/100 正确；
  rounds 中位数 8（最大 9）；T 中位数 827（SE 最大 1675，GWE 最大 1627）；uniform_majority 预算 2000。
## W0.5 exp1（E1 + E3 → results/*.json）

- 脚本：`paper/code/experiments.py`；算法：`graph_walk_elimination`（δ=0.05，k=3，完全图，θ 等距相邻间隔 Δ）。
- **每个配置/每点恰好 100 次重复**（实数记录，未取整），全部原始逐次数据在 JSON 的 `T_raw`/`success_raw` 中。
- 期间为达到"经验正确率 ≥95% 且不虚报"对算法 CI 做了两次实质修复（记录于 W0.4 节之后）：曲率下限 → 动态范围截断（D_MAX=2.0，有界 dynamic range 假设）+ Bernstein 线性项置信半径 + 活跃集内对比型淘汰（contrast CI：s²_ij = P_ii+P_jj−2P_ij）+ 采样聚焦活跃集（10% 全图混合防死锁）。每次修复后 7 个 pytest 仍全绿。
- **E1 结果（完全图，9 配置 × 100 次，成功率全部 1.00）**：

| n | Δ | T 均值 | 95% CI 半宽 | T/(n/Δ²) |
|---|---|---|---|---|
| 10 | 0.2 | 20912 | 1374 | 84 |
| 10 | 0.5 | 5508 | 242 | 138 |
| 10 | 1.0 | 2547 | 55 | 255 |
| 20 | 0.2 | 30890 | 1668 | 62 |
| 20 | 0.5 | 8429 | 421 | 105 |
| 20 | 1.0 | 3196 | 202 | 160 |
| 50 | 0.2 | 53080 | 3224 | 42 |
| 50 | 0.5 | 12259 | 550 | 61 |
| 50 | 1.0 | 5275 | 188 | 105 |

- E1 解读（诚实版）：固定 Δ 时 T 随 n **次线性**增长（Δ=0.2：n=10→50 只涨 2.5 倍，n 涨 5 倍）——与上界 O((n/Δ²)·log(n/δ)) 相容（早期淘汰使活跃集收缩，实测优于最坏情形常数）；T/(n/Δ²) 随 Δ 增大而上升（42→255），源于大 Δ 时有界动态范围截断的保守开销与 log 因子——上界允许这样（这是上界不是匹配下界的实测）。
- **E3 结果（n=20，完全图，Δ∈0.1..1.5 共 15 点 × 100 次，成功率全部 1.00）**：
  - 全范围 log-log 拟合斜率：**-1.377**（R²=0.9934，理论基准 -2）
  - 小间隙子范围 Δ∈[0.1,0.5]：**-1.557**（R²=0.9984）
  - σ'(Δ) 信息归一化后全范围：-1.192 / 小间隙：-1.523（归一化未缩小差距 → 大 Δ 端超出来自算法保守开销而非 BT 信息衰减）
- **斜率未到 -2 的原因（如实登记，Wave 1 待办）**：本 Wave 的置信区间是"插件 Fisher + Bernstein 线性项 + 有界范围截断"的保守启发式，其代价随 Δ 增大而增大（截断把饱和边的对比信息压到 σ'(D_MAX)）。理论目标 T ∝ Δ^{-2} 是信息论下界率；实测算法在两个保守设计（保正确率 100%）与指数拟合之间做了交换。Wave 1 用单侧饱和界替换截断后应回到 ≈ -2。
- JSON 中另含 `ci_level_pct: 95`（95% 置信区间标注，供 check_paper.py 核对正文中的 "95"）。

## W0.6 checker（check_paper.py 数字核验）

- 脚本：`paper/check_paper.py`。规则：扫描 `paper/**/*.tex` 非注释文本中的数字 token（小数 + ≥2 位整数），逐个到 `paper/results/*.json` 做词边界 grep（含浮点归一化重试）；未匹配 → 列出并**非零退出**。
- 刻意排除（结构性数字，非实验结果）：LaTeX 注释、`\cite/\ref/\eqref/\label/\url/...` 参数、`Theorem/Lemma/Table/Figure/Section/Algorithm/...` 后接的编号（含 `~` 连接）、裸年份 19xx/20xx。
- **自测（`--selftest`，临时文件用后即删）**：
  1. 临时 tex 植入假数字 **0.98765**（正文）+ **0.11111**（注释内）+ 真实数字（取自 e1.json 的 T_raw[0] 与 delta）→ 检出 0.98765 ✓、忽略注释内 0.11111 ✓；
  2. 干净 tex（只有真实数字 + 结构编号 `Theorem~4.1`、年份 2018、`\cite{...}`）→ 0 个未匹配 ✓；
  3. 自测输出：`planted fake 0.98765 flagged = True; comment-fake 0.11111 ignored = True; clean file has 0 unmatched = True`，exit 0。
  - 自测过程中发现并修复 checker 自身一个 bug：结构排除模式未覆盖 `Theorem~4.1` 的 LaTeX 不换行符 `~`（首轮自测报 clean 文件含未匹配 '4.1'）。
- **真实检查**：当前 `paper/` 下尚无 .tex（Wave 1/2 才写正文）→ `no .tex files under paper/ yet -- nothing to check (Wave 0); exit 0`。Wave 1 起每次编译前必须跑。

## Wave 0 完成情况表（验收对照 SPEC 第 9 节 + run-paper.sh）

| # | 任务 | 实际产出 | 验收 | 结果 |
|---|---|---|---|---|
| W0.1 | fetch_refs.py | `paper/fetch_refs.py`、`refs.bib`（35 条，全脚本生成）、`refs_raw.json`（35 篇摘要+引用数） | `grep -c '^@'` = 35 ≥ 25 ✓；每条有真实 arxiv_id（arXiv API 抓取时验证）✓；五方向查询全部实际执行 ✓ | 通过 |
| W0.2 | SURVEY（闸门） | `paper/SURVEY.md`（界清单 4 表 + 逐条对照 + 三选一结论）；结论写进本文件 | 每方向摘要阅读 ≥8（实际 35 篇全读）✓；三选一明确 = **第三条（保持原定位，附 5 条强制修订）**✓；未触发 STOP | 通过 |
| W0.3 | simulate.py | `paper/code/simulate.py`（BT 采样器 + 5 种图生成器 + eigvalsh 实测 λ_G） | 五种图 λ_G 已打印且与理论一致（complete=20=n ✓, star=1 ✓, cycle≈4π²/n² ✓, dumbbell 瓶颈小 ✓）| 通过 |
| W0.4 | algorithms.py | 三算法 + `test_algorithms.py`；调试修复 4 个真实 bug（标签方向/规范奇异/饱和发散/采样稀释+对比淘汰） | `pytest`: **7 passed**；n=5、Δ=2 与 Δ=1 易例上三算法各 100/100 正确；k∈{1,2,3}；稀疏图冒烟非 capped | 通过 |
| W0.5 | E1+E3 | `paper/results/e1.json`、`e3.json`（含全部逐次原始数据）；斜率写入上节 | E1 9 配置 × 100 次、E3 15 点 × 100 次（实数）✓；成功率全部 1.00 ✓；拟合斜率 -1.377/-1.557 已如实写入 ✓ | 通过（斜率与 -2 的差距已归因并列为 Wave 1 待办） |
| W0.6 | check_paper.py | `paper/check_paper.py` + 自测通过 | 植入假数字 0.98765 能检出 ✓、注释内假数字被忽略 ✓、干净文件 0 未匹配 ✓；真实检查（无 tex）exit 0 ✓ | 通过 |

**未完成项**：无。**Wave 1 风险提示**：(1) 定理 4.1 证明中 1/λ_G 项的推导是关键难点（SPEC 第 4 节）；(2) 算法置信区间需把"有界范围截断 + Bernstein 线性项"升级为单侧饱和界，才能让 E3 斜率回到 ≈ -2 并支撑 δ-正确性证明；(3) E2/E4/E5 未跑（属 Wave 1）；(4) 正文 tex 未写（属 Wave 1/2），check_paper.py 就绪待命。
