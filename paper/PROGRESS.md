# PROGRESS — Top-k Identification under Restricted Comparison Graphs

> 反伪造三规则（SPEC 第 6 节，贯穿全程）：
> 1. 论文正文每个数字必须能在 `paper/results/*.json` 中 grep 到，由 `paper/check_paper.py` 自动核验，不通过非零退出。
> 2. `refs.bib` 只能由 `paper/fetch_refs.py` 从 arXiv/S2 API 真实返回生成，禁止手写；`SURVEY.md` 提到的每篇论文必须在 `refs.bib` 中。
> 3. 定理证不完就标 Conjecture；实验跑多少次写多少次，不许虚报。
>
> 闸门：W0.2 SURVEY 若结论为"该方向已被紧界覆盖"，写 `[STOP]` + 创建 `paper/STOP`，后续任务全部停做。

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
