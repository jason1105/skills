# CHANGELOG

- 2.0.0 — 结构化重构：唯一权威数据模型节（B2 schema+JSON 样例+双投影映射表）；两套四节声明为投影关系并统一标题层级；AC 编号＝父 story.id 前缀；定位入口收敛 locateFromCard/locateFromAC；三种定位路径状态矩阵；六机制 pendingOp 判定标准；C1-C3 契约整合（徽标不变量/定位即展示四连/自然可达性 demo.path 可执行序列/覆盖阈值 90/10/5）；交付门 lint 七项+浏览器 G1-G5；git/MR/worktree 运维外移 references/ops-notes.md；事故注记统一〔事故〕短格式；输入判定三分支；Market 私锚定清理。依据：glm-5.3/5.4 两轮独立评审（13+17 findings，四个核心判断两轮收敛）
- 1.9.0 — 徽标一致性契约（全载体含弹窗）＋定位切换先关旧 modal
- 1.8.0 — 自然可达性契约（demo 载体禁演示孤岛）
- 1.7.0 — target schema 强制项（act/fn 二选一、落点无条件渲染）＋定位即展示契约＋产物 lint
- 1.6.0 — AC 级演示映射（demo 字段＋locateFromAC＋覆盖表交付门）
- 1.5.0 — 卡片四节式＋原型交互六机制（去项目私有锚定）
