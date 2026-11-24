---
name: workflow-model-strategy
description: >
  Workflow 子 agent 选模型策略表 —— 决定 workflow 脚本里每个 agent() 该配 haiku/sonnet/opus。
  含「基础策略」(planner/finder/reader/coder/refuter/judge/critic/synthesize/mechanical
  九类通用角色 → 模型)、「特殊策略」(React + Java 企业软件设计→编码流水线的阶段化调档)、
  以及「落地铁律」(选型如何落到 agent() 的 spawn 参数、fan-out 预算门控)。
  触发时机:准备写或修改 Workflow 脚本时、给 agent() 挑模型时、被 wf-model-gate hook
  拦下提示「裸 agent()」时、判断某个角色该升档到 opus 还是降档到 haiku 时。
---

# Workflow 选模型策略

> 本文原为 `~/.claude/CLAUDE.md` 常驻内容,2026-07-28 抽出为按需加载的 skill。
> CLAUDE.md 只保留两条结论,细则(为什么这么配、怎么调档)全在这里。
> 配套强制层:`~/.claude/hooks/wf-model-gate.py`(PreToolUse,拦裸 agent())。

选模型分两层:**基础策略**(通用角色,任何任务都套)叠加**特殊策略**(按场景细化、覆盖基础)。

### Workflows 基础策略 · 通用角色 → 模型

| 角色 | 模型 | 理由 |
| --- | --- | --- |
| planner / 拆解编排（切子任务、定 workflow 形状） | opus | 拆解质量是整个 workflow 的上限,错了全盘皆输——最该上配 |
| finder / recon（发散深挖、找问题） | sonnet | 要广度,中配够用且比 opus 省;并发多份时成本敏感 |
| reader / extract（读文件、摘录指定事实） | haiku | 锚点明确的纯搬运,无需判断——降到底 |
| coder / implement（按已定方案写代码） | sonnet（难点 opus） | 多数实现 sonnet 够;核心算法/并发/边界多再上 opus |
| refuter / verify（拿一条核对 file:line） | haiku（需判断时 sonnet） | 纯核对锚点用 haiku;张冠李戴/数量级低估这类判断要 sonnet,且换族 |
| judge / scorer（给 N 个方案打分排序） | sonnet | 要可比、要判断但收敛,sonnet 稳 |
| critic / completeness（找"还缺什么"） | sonnet | 要发散+判断,降配最易漏报 |
| synthesize / 终判（综合成报告、权衡） | sonnet（必要时 opus） | 通常 sonnet 足够;结论敏感再上 opus |
| mechanical / format（改名、格式化、样板） | haiku | 纯机械套路,降到底 |

> **降配的真正前提是「需求已被上游嚼碎成无歧义指令」,不是任务看着机械。** coder/verify/mechanical 表面是样板,底下常压着需求理解;agent 若要自己回去啃原始需求,haiku/sonnet 会"理解得似是而非、却把样板写得很标准"——最难发现的错。判据:这个 agent 拿到的是**已消化的明确指令还是原始需求**?拿指令才敢降配;拿原始需求,哪怕活看着简单也要上配。
>
> **对抗对要换族**(族 = 模型系列:haiku / sonnet / opus 各为一族,同系列不同版本不算换族):coder↔reviewer、finder↔refuter 若同模型,共享同一套盲区,评审/验证等于走过场。对抗式环节(评审、红队、互验)刻意让两边用不同模型族才有纠错价值。

### Workflows 特殊策略 · React + Java 企业软件(设计→编码流水线)

把基础角色落到具体阶段并按工程特性调档:**架构设计** = 判断最密的 planner、**代码评审** = refuter、**业务编码** = coder、**构建验证** = verify、**机械改造** = mechanical。开销决策核心是「设计该上 opus,编码该降到哪」。

| 阶段 | 模型 | 理由(相对基础策略的调整) |
| --- | --- | --- |
| 架构/方案设计（模块划分、分层、跨服务边界、技术选型、风险项） | opus | 我场景里 opus 唯一真正回本的环节——架构错了下游全返工,且最难逆转。主干服务边界、跨模块"必须走 service 层"这类约束必须上配 |
| 任务拆解（把方案切成可执行 task、定依赖顺序） | opus 或 sonnet | 方案稳时 sonnet 能拆;方案含糊、任务相互纠缠时上 opus |
| 接口/契约设计（前后端字段、错误码、分页/异步约定） | sonnet（复杂领域 opus） | 契约错会同时拖垮前后端;领域复杂(多态/版本演进)再上 opus |
| 库表/DDL 设计（索引、约束、迁移） | sonnet（迁移/大表 opus） | 线上 schema 难回滚,要谨慎核对;数据迁移、大表上 opus |
| 代码库调研（定位实现、调用链、找复用点与既有约定） | sonnet | 大库里要广度,并发跑多份省成本。"标识符回源核实"锚点明确处可派 haiku |
| 业务编码（Controller/Service/CRUD、React 页面/组件） | sonnet（核心逻辑 opus、纯样板 haiku） | 前提是上游 DESIGN.md/TODO.md 已把需求嚼碎;直接啃原始需求别降配。8 成分层样板 sonnet 够,升降配信号见下 |
| 代码评审（挑 bug、复用、简化） | sonnet,换族 | 必须和 coder 不同模型族,否则审不出自己写代码时的盲区 |
| 构建/自测验证（起服务、grep BUILD SUCCESS、跑用例、看页面） | haiku（行为判断 sonnet） | 核对锚点纯机械(BUILD SUCCESS 必 grep);判断"改对没、行为是否符合预期"才上 sonnet |
| 机械改造（批量重命名、格式化、迁移样板） | haiku | 纯套路,降到底 |

> **业务编码升 opus 的信号**(命中任一就别用 sonnet):Java——事务边界、并发、跨模块领域建模、复杂 SQL;React——跨组件状态编排、性能(re-render/虚拟化)、复杂异步或表单联动。其余分层 CRUD 与组件样板,sonnet 足够,改名式样板直接 haiku。
>
> **spec-coder 能降档,正因需求已在上游 DESIGN.md/TODO.md 消化完**——这是「降配前提」原则在本场景的落点:有设计文档兜底才敢降,没有就别拿低档模型啃原始需求写代码。

### Workflows 落地铁律 · 决策→执行的桥接

> 上面两张表是「决策层」(哪个角色配哪个模型),这一节是「执行层」(决策怎么落到 `agent()` 调用)。决策层完整不等于会落地——实测踩过:11 个裸 `agent()` 全默默继承了主 loop(Opus)。这两条门控堵住决策到调用之间的跨度。

- **选型必须落到 spawn 参数,不依赖默认继承。** workflow 的 `agent()` 不写模型就**继承主 loop**(通常 Opus)——这是默默吃 Opus 的缺省口子。两条旋钮各归其位:
  - reader / 只读调研(锚点明确的纯搬运)→ `agentType: 'Explore'`(只读 reader,**自带 haiku**,最自然的落地)
  - 需 sonnet/opus 的角色(**finder/recon**、coder/judge/planner/synthesize/对抗换族)→ 裸 `agent()` **必须显式写 `model: 'sonnet'|'opus'`**(finder/recon 走 sonnet,与基础策略表一致;别误并进 Explore/haiku)
  - **禁区:不存在"裸 `agent()` 不写 model"**——每个 `agent()` 二选一:走 Explore,或显式 model。漏写=继承 Opus。
- **fan-out 预算门控:宽度 > 3 前先估算 `N路 × 档位 × token/agent` 是否超 session 额度。** 超了**优先收窄宽度 / 同类目标打包给一个 agent / 分批**,而非降档牺牲质量。实测踩过:14 路 Opus 并行 752k token 直接撞爆 session limit——逐 agent 看选型没错,整体宽度×档位爆了。ultracode 下尤其要先算这一笔。


