# gene_tree
Input Figtree，Plot gene family expansion contraction with piechart 。
# Gene Family Gain/Loss Tree Plotter

一个纯前端网页工具，用于绘制带有 gene family expansion/contraction 信息的进化树。

## 功能

- 上传或粘贴 Newick
- 解析 `+gain/-loss`
- 叶标签清理
- rename 文件重命名
- 绘制矩形进化树
- 内部节点和叶节点饼图
- gain/loss 彩色数字
- MYA 坐标轴
- branch length 标签
- 图例和图例标题
- ladderize 控制
- 导出 SVG / PNG / PDF
- 保存和读取参数 JSON

## Newick 格式

节点或叶名称中需要包含：

```text  
+数字/-数字  