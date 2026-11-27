# CHANGELOG

- 2.0.4 — 逻辑不自洽事故驱动：C2 增「正常逻辑优先」（验证按钮必须标注「仅限需求验证」且样式区分，禁止冒充正常功能入口）与「seed 一致性」（派生渲染单一事实源，lint⑨ 对账）
- 2.0.3 — 评审修复轮③（round-3 六项）：FN_REGISTRY 键集改 node 沙箱 Object.keys 单次求值（根治字符串内括号/async 简写/注释三类误判，同时覆盖键集与求值崩溃检测）；④ AC 全格式断言＋1..n 连续；⑧ 描述补齐（goal/userStory/live path/act 存在性）；CHANGELOG 补 2.0.2
- 2.0.2 — 评审修复轮②（round-2 九项＋round-3 六项）：FN_REGISTRY 改 node 沙箱 Object.keys 提取（根治字符串内括号/async 简写两类误判）；dry-run 包装分流（async 箭头/function 原样包）；探针崩溃报红；④ AC 全格式断言＋1..n 连续；⑧ 增强（goal/userStory/live path/act 存在性）；版本化标题正则泛化；③ 档位限定 select#fault；死代码清理
- 2.0.1 — 评审修复轮①（round-1 13 项）：lint② dry-run 真跑 node；lint⑥ 剔除 STORIES 后按三类载体匹配；lint⑧ schema 校验；lint① data-id 守卫＋动态 id 降提示；MD 标题门（## REQ 二级红＋版本化节标题红）；lint⑦ 正则加严（AC\d+/全角空格/set+条数+重复）；B2 demo.note 字段；STORIES 纯 JSON 排版约束
- 2.0.0 — 结构化重构（breaking：卡片节标题不带版本号、版本进字段表，存量卡片需同步）：唯一权威数据模型节（B2 schema+JSON 样例+双投影映射表）；两套四节声明为投影关系并统一标题层级；AC 编号＝父 story.id 前缀；定位入口收敛 locateFromCard/locateFromAC；三种定位路径状态矩阵；六机制 pendingOp 判定标准；C1-C3 契约整合（徽标不变量/定位即展示四连/自然可达性 demo.path 可执行序列/覆盖阈值 90/10/5）；交付门 lint 七项+浏览器 G1-G5；git/MR/worktree 运维外移 references/ops-notes.md；事故注记统一〔事故〕短格式；输入判定三分支；Market 私锚定清理。依据：glm-5.3/5.4 两轮独立评审（13+17 findings，四个核心判断两轮收敛）
- 1.9.0 — 徽标一致性契约（全载体含弹窗）＋定位切换先关旧 modal
- 1.8.0 — 自然可达性契约（demo 载体禁演示孤岛）
- 1.7.0 — target schema 强制项（act/fn 二选一、落点无条件渲染）＋定位即展示契约＋产物 lint
- 1.6.0 — AC 级演示映射（demo 字段＋locateFromAC＋覆盖表交付门）
- 1.5.0 — 卡片四节式＋原型交互六机制（去项目私有锚定）
