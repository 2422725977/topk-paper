#!/bin/bash
# 论文《Top-k Identification under Restricted Comparison Graphs》无人值守执行脚本
# 闸门机制：若 W0.2 文献核实结论为"已被做透"，写 STOP 文件后后续步骤全部跳过
cd /Users/xi/Documents/topk-paper || exit 1
source ~/.zshrc >/dev/null 2>&1

mkdir -p /Users/xi/Documents/topk-paper/paper
LOG=/Users/xi/Documents/topk-paper/paper/run.log
GID=(-c user.name=xi -c user.email=70122327+2422725977@users.noreply.github.com)
P="工作目录 /Users/xi/Documents/topk-paper。先 read SPEC.md 全文，然后严格执行下面这一项任务，不要跳步、不要顺手做别的任务。这是独立仓库，绝对不要碰 /Users/xi/Documents/exam-diag 的任何文件。特别注意 SPEC.md 第 6 节反伪造约束。"

step () {
  local name="$1"; local task="$2"
  if [ -f paper/STOP ]; then
    echo "===== [$name] SKIPPED (STOP gate active) =====" >> "$LOG"
    return 0
  fi
  echo "" >> "$LOG"
  echo "===== [$name] START $(date '+%F %T') =====" >> "$LOG"
  dsh headless "$P

$task" >> "$LOG" 2>&1
  local rc=$?
  echo "===== [$name] END $(date '+%F %T') exit=$rc =====" >> "$LOG"
  git add -A >> "$LOG" 2>&1
  git "${GID[@]}" commit -q -m "paper($name): $(date '+%H:%M')" >> "$LOG" 2>&1
  if git push -q origin main >> "$LOG" 2>&1; then
    echo "PUSHED $(git rev-parse --short HEAD)" >> "$LOG"
  else
    echo "PUSH FAILED at [$name] — 下一步重试" >> "$LOG"
  fi
  return 0
}

echo "===== TOPK PAPER RUN $(date '+%F %T') =====" >> "$LOG"

step "refs" "完成 SPEC.md Wave 0 任务 W0.1：写 paper/fetch_refs.py，按 SPEC 第 3 节的五个检索方向从 arXiv API 抓论文元数据，再用 Semantic Scholar 补 citationCount，生成 paper/refs.bib。硬要求：BibTeX 只能由脚本从 API 真实返回的元数据生成，禁止手写任何条目；每个方向至少 8 篇，总计 25-35 篇；请求间 sleep 3 秒。跑完把 grep -c '@' refs.bib 的真实数字、每个方向的篇数写进 paper/PROGRESS.md。"

step "survey" "完成 SPEC.md Wave 0 任务 W0.2，这是整篇论文的闸门任务：读 refs.bib 覆盖的论文摘要（用 arXiv/S2 API 取 abstract），按 SPEC 第 3 节回答五个问题，写 paper/SURVEY.md。必须包含：1) 已有工作的样本复杂度界清单表（作者/年份/Setting/上界/下界）；2) 与你 SPEC 第 2 节初稿贡献的逐条差异对照；3) 明确选择三种定位中的一种并说明依据。**关键**：如果核实发现'受限于比较图的 Top-k 样本复杂度'已被已有工作紧界覆盖，就在 paper/SURVEY.md 开头写 [STOP] 并创建 paper/STOP 文件（内容是阻止继续的原因和建议），然后结束本任务。绝对不许为了产出而硬写一篇重复劳动的论文。"

step "sim" "完成 Wave 0 任务 W0.3：写 paper/code/simulate.py，包含 1) Bradley-Terry 采样器 cmp(i,j,theta) 返回胜者；2) 图生成器：complete_graph(n)、random_graph(n,p)、cycle_graph(n)、star_graph(n)、dumbbell_graph(n)；3) 用 numpy 计算每个图 Laplacian 的次小特征值 lambda_G 并打印。验证：完全图上 lambda_G 应约等于 n，环形图应约等于 0（连通但细长）。把五种图的实测 lambda_G 数值写进 PROGRESS.md。"

step "algo" "完成 Wave 0 任务 W0.4：写 paper/code/algorithms.py，实现三个算法：uniform_majority(theta, G, k, budget)（均匀随机采边+多数投票）、successive_elimination(theta, G, k, delta)（逐轮淘汰）、graph_walk_elimination(theta, G, k, delta)（你的算法：按图随机游走采边 + 置信区间淘汰）。再写 paper/code/test_algorithms.py：在 n=5、theta 差距明显（如 [2,1,0,-1,-2]）、完全图的易例上，断言三个算法都能 100% 正确返回 Top-k。跑 pytest 到全绿，把通过数量和实际迭代次数写进 PROGRESS.md。"

step "exp1" "完成 Wave 0 任务 W0.5 第一部分：写 paper/code/experiments.py 的 E1 和 E3。E1：完全图上 n in {10,20,50} x Delta in {0.2,0.5,1.0}，测达到 95% 正确率所需比较次数，每个配置 100 次重复。E3：固定 n=20、完全图，扫 Delta in 0.1..1.5，拟合 T 与 Delta 的幂律斜率（理论应为 -2）。结果写 paper/results/e1.json 与 e3.json，含每次重复的原始数据点。把拟合出的真实斜率和 E1 各格实测次数写进 PROGRESS.md。"

step "checker" "完成 Wave 0 任务 W0.6：写 paper/check_paper.py，正则扫描 paper/ 下所有 .tex 文件里的数字 token，逐个到 paper/results/*.json 核对；未匹配的列出并以非零退出。自测：临时造一个含假数字 0.98765 的 tex 文件，确认能检出，再删掉，把自测过程写进 PROGRESS.md。最后跑一次真实检查。"

step "wrap" "整理 paper/PROGRESS.md：汇总六个步骤的真实命令输出与数字，开头写反伪造三规则 + 闸门说明，末尾写 Wave 0 完成情况表（每项任务/实际产出/验收是否通过/未完成项与原因）。若 paper/STOP 存在，在表里明确写出『因文献核实发现问题，后续 Wave 1/2 不建议继续』。确认所有文件已 commit。"

echo "" >> "$LOG"
echo "===== TOPK PAPER WAVE 0 DONE $(date '+%F %T') =====" >> "$LOG"
