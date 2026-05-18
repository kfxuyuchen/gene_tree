网页工具地址：https://kfxuyuchen.github.io/gene_tree/
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

#关于进化树文件的准备，这里是提取的cafe5软件输出的结果，在.tre结尾的文件里，复制的是第一个进化树为后续用，保存为id_tree.txt

#clade添加前树处理

sed -E 's/(<[0-9]+>)[^:,;)]+/\1/g' id_tree.txt > cleaned_tree.txt 
#使用1tree_add_clade.py脚本进行clade添加.得到的进化树文件可用户后续进化树美化

可以使用本网页小工具绘制，也可以使用2plot_gain_loss_tree.py脚本绘制进化树

python 1tree_add_clade.py -h 查看帮助
python 2plot_gain_loss_tree.py -h查看帮助 
