## 规范说明
针对公司的开发需要，对commit message的撰写格式基本模式是按照<Type>(<Scope>): <Short description>的模式写的，其中<Type>是提交内容的类型，<Scope>是描述当前提交代码的影响范围，我们把其定义为所属的功能模块和对应禅道ID，而Short description则是对提交内容的概要描述。当然，如果概要描述无法描述清楚本次提交的内容，我们可以在换行后添加<Long description>撰写更详细的描述。</br>

- Type的种类： 
  - feat: 增加新功能 
  - fix: bug的修复 
  - docs: 文档的添加或修改
  - style: 不影响代码功能的代码格式变化
  - refactor: 代码的重构
  - perf: 提升性能的代码
  - test: 增加测试用例
  - build: 项目构建相关的代码
  - ci: 持续集成相关的代码
  - chore: 其他一些不影响源码的提交
  - revert: 提交的回滚

- Scope格式一般为：影响功能模块 禅道ID，例子如下（多个禅道ID列表之间用逗号隔开，bug#，story#，task#是必须标注的）：

  - 模拟出清 task#1234
  - 运行场景 bug#3214
  - 市场体系 story#1235
  - 单机模拟 bug#12312

## Commit方式
  关于Commit方式同样需要规范化：
1. 清晰描述commit的内容，不同类型或不同功能的内容 分开多次提交 （IDEA或者VSCode都支持单个文件选择部分内容进行stage和commit）；
2. 根据commit message提交文件，不掺杂commit message描述以外的内容；
3. 同一个文件的移动文件夹操作与重命名或者文件内容大量修改操作需要尽量分开进行commit，为了能识别文件变化操作是移动而不是删除文件并新增新的文件，这样能尽量保存文件的修改历史； 
4. 示例：
   - feat(创建单机模拟 task#10932):创建单机模拟，根据机组类型报价增加水电； 
   - fix(智能代理 bug#7707):修复智能代理设置的训练次数和收益次数不符合的问题。