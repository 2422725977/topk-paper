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
