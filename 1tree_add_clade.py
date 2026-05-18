#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
功能：将Base_clade_results.txt中的增长/减少数值注释到进化树文件节点上
输出：带注释的新树文件
"""

import re
import sys
import argparse

def main():
    # ===================== 命令行参数与帮助信息 =====================
    parser = argparse.ArgumentParser(
        description="""
【进化树节点注释工具】
功能：将 clade 结果中的增长（increase）、减少（decrease）数值自动标注到进化树节点上
支持两种节点格式：
  1. 物种节点：Vvi<1>  →  Vvi<1>+1536/-4918
  2. 内部节点：<22>    →  <22>+220/-334
""",
        formatter_class=argparse.RawTextHelpFormatter
    )

    # 必选参数
    parser.add_argument(
        "-c", "--clade",
        required=True,
        help="输入：Clade结果文件（如 Base_clade_results.txt）\n格式：taxon_id   increase   decrease"
    )
    parser.add_argument(
        "-t", "--tree",
        required=True,
        help="输入：进化树文件（如 cleaned_tree.txt）\n格式：Newick格式树"
    )

    # 可选参数
    parser.add_argument(
        "-o", "--output",
        default="cleaned_tree_with_gamma.txt",
        help="输出：注释后的树文件（默认：cleaned_tree_with_gamma.txt）"
    )

    # 如果没有参数，打印帮助
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    # ===================== 读取 clade 结果 =====================
    print(f"正在读取 clade 文件：{args.clade}")
    gamma_data = {}

    try:
        with open(args.clade, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"错误：无法读取文件 {args.clade} → {e}")
        sys.exit(1)

    # 跳过标题行，读取数据
    for idx, line in enumerate(lines[1:], 2):
        line = line.strip()
        if not line:
            continue

        parts = line.split()
        if len(parts) >= 3:
            taxon_id = parts[0]
            increase = parts[1]
            decrease = parts[2]
            gamma_data[taxon_id] = (increase, decrease)
        else:
            print(f"警告：第 {idx} 列数不足，已跳过 → {line}")

    if not gamma_data:
        print("错误：未读取到任何有效节点数据！")
        sys.exit(1)

    print(f"成功读取 {len(gamma_data)} 个节点的注释信息")

    # ===================== 读取进化树 =====================
    print(f"正在读取树文件：{args.tree}")
    try:
        with open(args.tree, 'r', encoding='utf-8') as f:
            tree_content = f.read()
    except Exception as e:
        print(f"错误：无法读取树文件 {args.tree} → {e}")
        sys.exit(1)

    # ===================== 替换节点 =====================
    print("开始注释节点...")
    for taxon_id, (increase, decrease) in gamma_data.items():

        # 匹配：Vvi<1> 或 <22>
        if re.match(r'^[A-Za-z]+<\d+>$', taxon_id) or re.match(r'^<\d+>$', taxon_id):
            pattern = re.escape(taxon_id)
            replacement = f"{taxon_id}+{increase}/-{decrease}"
            tree_content = re.sub(pattern, replacement, tree_content)

    # ===================== 输出结果 =====================
    print(f"正在保存结果：{args.output}")
    try:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(tree_content)
    except Exception as e:
        print(f"错误：无法写入输出文件 → {e}")
        sys.exit(1)

    print("=" * 50)
    print("✅ 任务完成！")
    print(f"输入clade：{args.clade}")
    print(f"输入树：{args.tree}")
    print(f"输出树：{args.output}")
    print("=" * 50)

if __name__ == "__main__":
    main()