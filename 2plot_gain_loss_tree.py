#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import argparse
from Bio import Phylo
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge, Patch
from matplotlib.offsetbox import (
    DrawingArea,
    AnnotationBbox,
    TextArea,
    HPacker
)


def parse_gain_loss(name):
    """
    Parse gain/loss information from node name.

    Examples:
        Athali<17>+2094/-1990
        <33>+493/-731
        Atrich+1362/-3284
    """
    if name is None:
        return 0, 0

    m = re.search(r"\+(\d+)/-(\d+)", name)

    if m:
        return int(m.group(1)), int(m.group(2))

    return 0, 0


def clean_label(name):
    """
    Clean leaf label.

    Examples:
        Athali<17>+2094/-1990 -> Athali
        Atrich+1362/-3284 -> Atrich
        <33>+493/-731 -> ""
    """
    if name is None:
        return ""

    name = re.sub(r"\+(\d+)/-(\d+)", "", name)
    name = re.sub(r"<[^>]*>", "", name)

    return name.strip()


def read_rename_file(rename_file):
    """
    Read a rename file.

    Format:
        old_name    new name can contain spaces

    Notes:
        1. The first field is the old name.
        2. The remaining text after the first whitespace is used as the new name.
        3. Tab and spaces are both supported.
        4. Empty lines and lines starting with # are ignored.
    """
    rename_dict = {}

    if rename_file is None:
        return rename_dict

    with open(rename_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")

            if not line.strip():
                continue

            if line.lstrip().startswith("#"):
                continue

            parts = re.split(r"\s+", line.strip(), maxsplit=1)

            if len(parts) < 2:
                continue

            old_name, new_name = parts[0].strip(), parts[1].strip()
            rename_dict[old_name] = new_name

    return rename_dict


def rename_leaf_label(label, rename_dict):
    """
    Rename leaf label according to rename_dict.
    """
    if label in rename_dict:
        return rename_dict[label]

    return label


def add_pie(
    ax,
    x,
    y,
    gain,
    loss,
    size=18,
    gain_color="#d62728",
    loss_color="#1f77b4"
):
    """
    Add a pie chart at data coordinate (x, y).
    """
    total = gain + loss

    if total <= 0:
        return

    da = DrawingArea(size, size, 0, 0)

    center = size / 2
    radius = size / 2

    gain_angle = 360 * gain / total

    # Loss as full background circle
    da.add_artist(
        Wedge(
            center=(center, center),
            r=radius,
            theta1=0,
            theta2=360,
            facecolor=loss_color,
            edgecolor="white",
            linewidth=0.4
        )
    )

    # Gain part
    da.add_artist(
        Wedge(
            center=(center, center),
            r=radius,
            theta1=90,
            theta2=90 + gain_angle,
            facecolor=gain_color,
            edgecolor="white",
            linewidth=0.4
        )
    )

    ab = AnnotationBbox(
        da,
        (x, y),
        frameon=False,
        box_alignment=(0.5, 0.5),
        zorder=5
    )

    ax.add_artist(ab)


def add_colored_gain_loss_text(
    ax,
    x,
    y,
    gain,
    loss,
    gain_color,
    loss_color,
    slash_color="#333333",
    fontsize=7,
    xybox=(0, 0),
    box_alignment=(0.5, 0.0),
    background=True,
    background_color="white"
):
    """
    Add compact colored text:
        +gain / -loss
    """
    plus_text = TextArea(
        f"+{gain}",
        textprops=dict(
            color=gain_color,
            fontsize=fontsize
        )
    )

    slash_text = TextArea(
        "/",
        textprops=dict(
            color=slash_color,
            fontsize=fontsize
        )
    )

    minus_text = TextArea(
        f"-{loss}",
        textprops=dict(
            color=loss_color,
            fontsize=fontsize
        )
    )

    packed = HPacker(
        children=[plus_text, slash_text, minus_text],
        align="center",
        pad=0,
        sep=1
    )

    if background:
        bboxprops = dict(
            facecolor=background_color,
            edgecolor="none",
            alpha=0.78,
            boxstyle="round,pad=0.12"
        )
    else:
        bboxprops = None

    ab = AnnotationBbox(
        packed,
        (x, y),
        xybox=xybox,
        xycoords="data",
        boxcoords="offset points",
        frameon=background,
        bboxprops=bboxprops,
        box_alignment=box_alignment,
        zorder=8
    )

    ax.add_artist(ab)


def get_x_positions_root_left(tree):
    """
    Keep Bio.Phylo depth:
        root = 0
        leaves = max_x

    Therefore, root is on the left and leaves are on the right.
    """
    depths = tree.depths()

    if max(depths.values()) == 0:
        depths = tree.depths(unit_branch_lengths=True)

    max_x = max(depths.values())

    return depths, max_x


def get_y_positions(tree):
    """
    Calculate y positions.
    Leaves are equally spaced.
    Internal nodes are placed at the mean y-position of their children.
    """
    terminals = tree.get_terminals()

    y_pos = {}

    for i, leaf in enumerate(terminals):
        y_pos[leaf] = i

    def calc_y(clade):
        if clade in y_pos:
            return y_pos[clade]

        child_ys = [calc_y(child) for child in clade.clades]
        y_pos[clade] = sum(child_ys) / len(child_ys)

        return y_pos[clade]

    calc_y(tree.root)

    return y_pos


def add_branch_length_text(
    ax,
    parent,
    child,
    x_pos,
    y_pos,
    fontsize=6,
    color="#555555",
    y_offset_points=1,
    background_color="white"
):
    """
    Add branch length label above the middle of a horizontal branch.

    y_offset_points controls the vertical distance between
    the branch line and the branch length text.
    """
    if child.branch_length is None:
        return

    x1 = x_pos[parent]
    x2 = x_pos[child]
    y = y_pos[child]

    mid_x = (x1 + x2) / 2

    ax.annotate(
        f"{child.branch_length:.2f}",
        xy=(mid_x, y),
        xytext=(0, y_offset_points),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=fontsize,
        color=color,
        zorder=7,
        bbox=dict(
            facecolor=background_color,
            edgecolor="none",
            alpha=0.75,
            pad=0.15
        )
    )


def draw_tree(
    ax,
    clade,
    x_pos,
    y_pos,
    line_color="black",
    lw=1.2,
    show_branch_length=False,
    branch_length_size=6,
    branch_length_color="#555555",
    branch_length_bg_color="white",
    branch_length_offset=1
):
    """
    Draw rectangular phylogenetic tree.
    """
    x = x_pos[clade]

    if clade.clades:
        child_ys = [y_pos[c] for c in clade.clades]

        ax.plot(
            [x, x],
            [min(child_ys), max(child_ys)],
            color=line_color,
            lw=lw,
            zorder=1
        )

        for child in clade.clades:
            cx = x_pos[child]
            cy = y_pos[child]

            ax.plot(
                [x, cx],
                [cy, cy],
                color=line_color,
                lw=lw,
                zorder=1
            )

            if show_branch_length:
                add_branch_length_text(
                    ax=ax,
                    parent=clade,
                    child=child,
                    x_pos=x_pos,
                    y_pos=y_pos,
                    fontsize=branch_length_size,
                    color=branch_length_color,
                    background_color=branch_length_bg_color,
                    y_offset_points=branch_length_offset
                )

            draw_tree(
                ax=ax,
                clade=child,
                x_pos=x_pos,
                y_pos=y_pos,
                line_color=line_color,
                lw=lw,
                show_branch_length=show_branch_length,
                branch_length_size=branch_length_size,
                branch_length_color=branch_length_color,
                branch_length_bg_color=branch_length_bg_color,
                branch_length_offset=branch_length_offset
            )


def node_text_offset_points(index):
    """
    Generate text offsets for internal node labels to reduce overlap.
    """
    offsets = [
        (0, 10),
        (0, 14),
        (0, 18),
        (8, 12),
        (-8, 12),
        (12, 16),
        (-12, 16)
    ]

    return offsets[index % len(offsets)]


def make_integer_mya_ticks(max_x, tick_interval=None, max_ticks=8):
    """
    Generate integer MYA ticks.

    Coordinate:
        root = 0
        leaf = max_x

    Display:
        leaf = 0 MYA
        root = max_x MYA
    """
    max_mya = int(round(max_x))

    if max_mya <= 0:
        return [max_x], ["0"]

    if tick_interval is not None and tick_interval > 0:
        interval = int(tick_interval)
    else:
        raw_interval = max_mya / max(max_ticks - 1, 1)

        nice_intervals = [
            1, 2, 5,
            10, 20, 25, 50,
            100, 200, 500, 1000
        ]

        interval = nice_intervals[-1]

        for ni in nice_intervals:
            if ni >= raw_interval:
                interval = ni
                break

    mya_values = list(range(0, max_mya + 1, interval))

    if 0 not in mya_values:
        mya_values.insert(0, 0)

    if max_mya not in mya_values:
        mya_values.append(max_mya)

    mya_values = sorted(set(mya_values))

    tick_positions = [max_x - v for v in mya_values]

    tick_positions = [
        min(max(pos, 0), max_x)
        for pos in tick_positions
    ]

    tick_labels = [str(int(v)) for v in mya_values]

    return tick_positions, tick_labels


def plot_gain_loss_tree(
    tree_file,
    output,
    fig_width=14,
    fig_height=9,
    pie_size=18,
    label_size=9,
    node_text_size=7,
    branch_width=1.2,
    gain_color="#d62728",
    loss_color="#1f77b4",
    slash_color="#333333",
    leaf_label_color="black",
    label_bg_color="white",
    text_bg_color="white",
    legend_loc="upper left",
    legend_anchor=None,
    show_legend=True,
    title_text=None,
    title_size=10,
    tick_interval=None,
    max_ticks=8,
    no_ladderize=False,
    leaf_label_gap=0.025,
    leaf_pie_gap=0.02,
    leaf_text_gap=0.02,
    rename_file=None,
    show_branch_length=False,
    branch_length_size=6,
    branch_length_color="#555555",
    branch_length_bg_color="white",
    branch_length_offset=1
):
    tree = Phylo.read(tree_file, "newick")

    rename_dict = read_rename_file(rename_file)

    if not no_ladderize:
        tree.ladderize(reverse=True)

    x_pos, max_x = get_x_positions_root_left(tree)
    y_pos = get_y_positions(tree)

    terminals = tree.get_terminals()
    max_y = max(y_pos.values())

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))

    # =========================
    # 1. Draw branches
    # =========================
    draw_tree(
        ax=ax,
        clade=tree.root,
        x_pos=x_pos,
        y_pos=y_pos,
        lw=branch_width,
        show_branch_length=show_branch_length,
        branch_length_size=branch_length_size,
        branch_length_color=branch_length_color,
        branch_length_bg_color=branch_length_bg_color,
        branch_length_offset=branch_length_offset
    )

    # =========================
    # 2. Leaf annotation layout
    # =========================
    labels = [
        rename_leaf_label(clean_label(leaf.name), rename_dict)
        for leaf in terminals
    ]

    max_label_len = max([len(x) for x in labels]) if labels else 5

    label_x = max_x + max(max_x * leaf_label_gap, 2.0)

    label_width_est = max(max_x * 0.006 * max_label_len, 3.0)

    leaf_pie_x = label_x + label_width_est + max(max_x * leaf_pie_gap, 2.5)
    leaf_text_x = leaf_pie_x + max(max_x * leaf_text_gap, 3.0)

    # =========================
    # 3. Internal node pies and labels
    # =========================
    internal_index = 0

    for clade in tree.find_clades(order="preorder"):
        if clade.is_terminal():
            continue

        gain, loss = parse_gain_loss(clade.name)

        if gain + loss <= 0:
            continue

        x = x_pos[clade]
        y = y_pos[clade]

        add_pie(
            ax=ax,
            x=x,
            y=y,
            gain=gain,
            loss=loss,
            size=pie_size,
            gain_color=gain_color,
            loss_color=loss_color
        )

        xybox = node_text_offset_points(internal_index)

        add_colored_gain_loss_text(
            ax=ax,
            x=x,
            y=y,
            gain=gain,
            loss=loss,
            gain_color=gain_color,
            loss_color=loss_color,
            slash_color=slash_color,
            fontsize=node_text_size,
            xybox=xybox,
            box_alignment=(0.5, 0.0),
            background=True,
            background_color=text_bg_color
        )

        internal_index += 1

    # =========================
    # 4. Leaf labels, pies and numbers
    # =========================
    for leaf in terminals:
        y = y_pos[leaf]

        label = rename_leaf_label(clean_label(leaf.name), rename_dict)
        gain, loss = parse_gain_loss(leaf.name)

        ax.text(
            label_x,
            y,
            label,
            fontsize=label_size,
            fontstyle="italic",
            ha="left",
            va="center",
            color=leaf_label_color,
            zorder=4,
            bbox=dict(
                facecolor=label_bg_color,
                edgecolor="none",
                alpha=0.65,
                pad=0.4
            )
        )

        add_pie(
            ax=ax,
            x=leaf_pie_x,
            y=y,
            gain=gain,
            loss=loss,
            size=pie_size,
            gain_color=gain_color,
            loss_color=loss_color
        )

        if gain + loss > 0:
            add_colored_gain_loss_text(
                ax=ax,
                x=leaf_text_x,
                y=y,
                gain=gain,
                loss=loss,
                gain_color=gain_color,
                loss_color=loss_color,
                slash_color=slash_color,
                fontsize=node_text_size,
                xybox=(0, -4),
                box_alignment=(0.0, 0.5),
                background=True,
                background_color=text_bg_color
            )

    # =========================
    # 5. Axis range
    # =========================
    right_extra = (leaf_text_x - max_x) + max(max_x * 0.12, 8)
    left_extra = max(max_x * 0.03, 2)

    ax.set_xlim(-left_extra, max_x + right_extra)
    ax.set_ylim(-1, max_y + 1)

    ax.invert_yaxis()

    # =========================
    # 6. Axis style and MYA ticks
    # =========================
    ax.yaxis.set_visible(False)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_visible(True)

    ax.spines["bottom"].set_bounds(0, max_x)

    tick_positions, tick_labels = make_integer_mya_ticks(
        max_x=max_x,
        tick_interval=tick_interval,
        max_ticks=max_ticks
    )

    ax.set_xticks(tick_positions)
    ax.set_xticklabels(tick_labels)

    ax.set_xlabel("MYA", fontsize=10)

    ax.tick_params(
        axis="x",
        which="major",
        direction="out",
        length=4,
        width=0.8,
        labelsize=8,
        bottom=True,
        top=False
    )

    # =========================
    # 7. Legend
    # =========================
    if show_legend:
        legend_handles = [
            Patch(
                facecolor=gain_color,
                edgecolor="none",
                label="Expansion"
            ),
            Patch(
                facecolor=loss_color,
                edgecolor="none",
                label="Contraction"
            )
        ]

        legend_kwargs = dict(
            handles=legend_handles,
            frameon=False,
            loc=legend_loc,
            fontsize=9
        )

        # Important:
        # --title-text is displayed above the legend.
        # It follows --legend-loc and --legend-anchor.
        if title_text:
            legend_kwargs["title"] = title_text
            legend_kwargs["title_fontsize"] = title_size

        if legend_anchor is not None:
            legend_kwargs["bbox_to_anchor"] = legend_anchor

        ax.legend(**legend_kwargs)

    # =========================
    # 8. Figure title
    # =========================
    # No ax.set_title() here.
    # --title-text is now used as the legend title.

    plt.tight_layout()
    plt.savefig(output, dpi=300, bbox_inches="tight")
    plt.close()


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Plot gene family expansion and contraction on a phylogenetic tree.\n\n"
            "This script reads a Newick tree containing gain/loss information in node names,\n"
            "such as '+2094/-1990', and draws a rectangular phylogenetic tree with pie charts\n"
            "and colored gain/loss numbers.\n\n"
            "Tree direction:\n"
            "  root on the left, leaves on the right.\n\n"
            "X-axis:\n"
            "  leaf position = 0 MYA\n"
            "  root direction = older time\n"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(
            "Input Newick name examples:\n"
            "  Athali<17>+2094/-1990\n"
            "  Atrich+1362/-3284\n"
            "  <33>+493/-731\n\n"
            "Basic usage:\n"
            "  python plot_gain_loss_tree.py -i tree.nwk -o result.pdf\n\n"
            "Use rename file:\n"
            "  python plot_gain_loss_tree.py \\\n"
            "    -i tree.nwk \\\n"
            "    -o result.pdf \\\n"
            "    --rename-file rename.tsv\n\n"
            "Rename file example:\n"
            "  Athali    Arabidopsis thaliana\n"
            "  Atrich    Amborella trichopoda\n"
            "  Osati     Oryza sativa japonica\n\n"
            "Show branch lengths:\n"
            "  python plot_gain_loss_tree.py \\\n"
            "    -i tree.nwk \\\n"
            "    -o result.pdf \\\n"
            "    --show-branch-length\n\n"
            "Adjust branch length label offset:\n"
            "  python plot_gain_loss_tree.py \\\n"
            "    -i tree.nwk \\\n"
            "    -o result.pdf \\\n"
            "    --show-branch-length \\\n"
            "    --branch-length-offset 2\n\n"
            "Change gain/loss colors:\n"
            "  python plot_gain_loss_tree.py \\\n"
            "    -i tree.nwk \\\n"
            "    -o result.pdf \\\n"
            "    --gain-color '#D55E00' \\\n"
            "    --loss-color '#0072B2'\n\n"
            "Set MYA tick interval:\n"
            "  python plot_gain_loss_tree.py \\\n"
            "    -i tree.nwk \\\n"
            "    -o result.pdf \\\n"
            "    --tick-interval 10\n\n"
            "Add text above legend:\n"
            "  python plot_gain_loss_tree.py \\\n"
            "    -i tree.nwk \\\n"
            "    -o result.pdf \\\n"
            "    --title-text 'Gene family changes'\n\n"
            "Move legend and its title:\n"
            "  python plot_gain_loss_tree.py \\\n"
            "    -i tree.nwk \\\n"
            "    -o result.pdf \\\n"
            "    --title-text 'Gene family changes' \\\n"
            "    --legend-loc upper right\n\n"
            "Use precise legend anchor:\n"
            "  python plot_gain_loss_tree.py \\\n"
            "    -i tree.nwk \\\n"
            "    -o result.pdf \\\n"
            "    --title-text 'Gene family changes' \\\n"
            "    --legend-loc upper left \\\n"
            "    --legend-anchor 0.03 0.97\n\n"
            "Adjust leaf label/pie/text spacing:\n"
            "  python plot_gain_loss_tree.py \\\n"
            "    -i tree.nwk \\\n"
            "    -o result.pdf \\\n"
            "    --leaf-label-gap 0.02 \\\n"
            "    --leaf-pie-gap 0.02 \\\n"
            "    --leaf-text-gap 0.02\n\n"
            "Notes:\n"
            "  1. Gain/loss information must be written as +number/-number.\n"
            "  2. Leaf labels are cleaned by removing '<...>' and '+gain/-loss'.\n"
            "  3. In rename file, the first field is the old name, and the rest is the new name.\n"
            "  4. Rename file supports tab or space separation.\n"
            "  5. New names may contain spaces.\n"
            "  6. Use quotes around color codes, for example '#D55E00'.\n"
            "  7. Branch length labels are placed above branches when --show-branch-length is used.\n"
            "  8. Use --branch-length-offset to adjust the vertical distance from branch lines.\n"
        )
    )

    parser.add_argument(
        "-i",
        "--input",
        required=True,
        metavar="TREE.nwk",
        help=(
            "Input Newick tree file.\n"
            "Node or leaf names may contain gain/loss information, for example:\n"
            "  Athali<17>+2094/-1990\n"
            "  Atrich+1362/-3284\n"
            "  <33>+493/-731"
        )
    )

    parser.add_argument(
        "-o",
        "--output",
        default="gene_family_gain_loss_tree.pdf",
        metavar="OUTPUT",
        help=(
            "Output figure file name.\n"
            "The format is determined by the file extension.\n"
            "Examples:\n"
            "  result.pdf\n"
            "  result.png\n"
            "  result.svg\n"
            "Default: gene_family_gain_loss_tree.pdf"
        )
    )

    parser.add_argument(
        "--width",
        type=float,
        default=14,
        metavar="FLOAT",
        help=(
            "Figure width in inches.\n"
            "Increase this value if leaf labels or right-side annotations are crowded.\n"
            "Default: 14"
        )
    )

    parser.add_argument(
        "--height",
        type=float,
        default=9,
        metavar="FLOAT",
        help=(
            "Figure height in inches.\n"
            "Increase this value if there are many species or leaves are too close.\n"
            "Default: 9"
        )
    )

    parser.add_argument(
        "--pie-size",
        type=int,
        default=18,
        metavar="INT",
        help=(
            "Pie chart size in points/pixels.\n"
            "This controls both internal-node pies and leaf pies.\n"
            "Default: 18"
        )
    )

    parser.add_argument(
        "--label-size",
        type=float,
        default=9,
        metavar="FLOAT",
        help=(
            "Font size of leaf labels.\n"
            "Default: 9"
        )
    )

    parser.add_argument(
        "--text-size",
        type=float,
        default=7,
        metavar="FLOAT",
        help=(
            "Font size of gain/loss number labels such as +2094/-1990.\n"
            "Default: 7"
        )
    )

    parser.add_argument(
        "--branch-width",
        type=float,
        default=1.2,
        metavar="FLOAT",
        help=(
            "Line width of tree branches.\n"
            "Default: 1.2"
        )
    )

    parser.add_argument(
        "--gain-color",
        default="#d62728",
        metavar="COLOR",
        help=(
            "Color for expansion/gain.\n"
            "Used for gain pies, '+gain' text, and Expansion legend patch.\n"
            "Default: #d62728"
        )
    )

    parser.add_argument(
        "--loss-color",
        default="#1f77b4",
        metavar="COLOR",
        help=(
            "Color for contraction/loss.\n"
            "Used for loss pies, '-loss' text, and Contraction legend patch.\n"
            "Default: #1f77b4"
        )
    )

    parser.add_argument(
        "--slash-color",
        default="#333333",
        metavar="COLOR",
        help=(
            "Color of the slash '/' between +gain and -loss numbers.\n"
            "Default: #333333"
        )
    )

    parser.add_argument(
        "--leaf-label-color",
        default="black",
        metavar="COLOR",
        help=(
            "Color of leaf species labels.\n"
            "Default: black"
        )
    )

    parser.add_argument(
        "--label-bg-color",
        default="white",
        metavar="COLOR",
        help=(
            "Background color behind leaf labels.\n"
            "Default: white"
        )
    )

    parser.add_argument(
        "--text-bg-color",
        default="white",
        metavar="COLOR",
        help=(
            "Background color behind gain/loss number labels.\n"
            "Default: white"
        )
    )

    parser.add_argument(
        "--legend-loc",
        default="upper left",
        choices=[
            "best",
            "upper right",
            "upper left",
            "lower left",
            "lower right",
            "right",
            "center left",
            "center right",
            "lower center",
            "upper center",
            "center"
        ],
        help=(
            "Legend location.\n"
            "The --title-text will be displayed above the legend and follows this location.\n"
            "Default: upper left"
        )
    )

    parser.add_argument(
        "--legend-anchor",
        nargs=2,
        type=float,
        metavar=("X", "Y"),
        default=None,
        help=(
            "Optional precise legend anchor position.\n"
            "This is passed to matplotlib bbox_to_anchor.\n"
            "Example:\n"
            "  --legend-anchor 0.02 0.98\n"
            "The --title-text follows the anchored legend.\n"
            "Default: not used"
        )
    )

    parser.add_argument(
        "--hide-legend",
        action="store_true",
        help=(
            "Hide the Expansion/Contraction legend.\n"
            "If this option is used, --title-text will also not be shown because it is attached to the legend."
        )
    )

    parser.add_argument(
        "--title-text",
        default=None,
        metavar="TEXT",
        help=(
            "Text displayed above the legend.\n"
            "It follows the legend position controlled by --legend-loc and --legend-anchor.\n"
            "Example:\n"
            "  --title-text 'Gene family changes'\n"
            "Default: no legend title"
        )
    )

    parser.add_argument(
        "--title-size",
        type=float,
        default=10,
        metavar="FLOAT",
        help=(
            "Font size of the legend title specified by --title-text.\n"
            "Default: 10"
        )
    )

    parser.add_argument(
        "--tick-interval",
        type=int,
        default=None,
        metavar="INT",
        help=(
            "Integer interval for MYA ticks.\n"
            "Examples:\n"
            "  --tick-interval 10\n"
            "  --tick-interval 20\n"
            "If not set, the script automatically chooses a suitable interval.\n"
            "Default: auto"
        )
    )

    parser.add_argument(
        "--max-ticks",
        type=int,
        default=8,
        metavar="INT",
        help=(
            "Maximum approximate number of x-axis ticks in automatic mode.\n"
            "Only used when --tick-interval is not specified.\n"
            "Default: 8"
        )
    )

    parser.add_argument(
        "--leaf-label-gap",
        type=float,
        default=0.025,
        metavar="FLOAT",
        help=(
            "Gap between leaf node end and leaf label.\n"
            "Value is a fraction of tree width.\n"
            "Default: 0.025"
        )
    )

    parser.add_argument(
        "--leaf-pie-gap",
        type=float,
        default=0.02,
        metavar="FLOAT",
        help=(
            "Gap between leaf label and leaf pie chart.\n"
            "Value is a fraction of tree width.\n"
            "Default: 0.02"
        )
    )

    parser.add_argument(
        "--leaf-text-gap",
        type=float,
        default=0.02,
        metavar="FLOAT",
        help=(
            "Gap between leaf pie chart and gain/loss text.\n"
            "Value is a fraction of tree width.\n"
            "Default: 0.02"
        )
    )

    parser.add_argument(
        "--rename-file",
        default=None,
        metavar="FILE",
        help=(
            "Two-column file for renaming leaf labels.\n"
            "Format:\n"
            "  old_name    new name can contain spaces\n\n"
            "The old_name should match the cleaned leaf label, after removing '<...>' and '+gain/-loss'.\n"
            "Separators can be tab or spaces.\n"
            "Only the first whitespace is used to split old_name and new_name.\n"
            "Therefore, new names may contain spaces.\n"
            "Example:\n"
            "  Athali    Arabidopsis thaliana\n"
            "  Osati     Oryza sativa japonica"
        )
    )

    parser.add_argument(
        "--show-branch-length",
        action="store_true",
        help=(
            "Show branch lengths on branches.\n"
            "Values are rounded to two decimal places.\n"
            "Branch length labels are displayed above horizontal branches."
        )
    )

    parser.add_argument(
        "--branch-length-size",
        type=float,
        default=6,
        metavar="FLOAT",
        help=(
            "Font size for branch length labels.\n"
            "Default: 6"
        )
    )

    parser.add_argument(
        "--branch-length-color",
        default="#555555",
        metavar="COLOR",
        help=(
            "Color for branch length labels.\n"
            "Default: #555555"
        )
    )

    parser.add_argument(
        "--branch-length-bg-color",
        default="white",
        metavar="COLOR",
        help=(
            "Background color for branch length labels.\n"
            "Default: white"
        )
    )

    parser.add_argument(
        "--branch-length-offset",
        type=float,
        default=1,
        metavar="FLOAT",
        help=(
            "Vertical offset of branch length labels above branches, in points.\n"
            "Larger values move labels farther away from branch lines.\n"
            "Smaller values make labels closer to branch lines.\n"
            "Default: 1"
        )
    )

    parser.add_argument(
        "--no-ladderize",
        action="store_true",
        help=(
            "Do not ladderize the tree.\n"
            "By default, the tree is ladderized with reverse=True.\n"
            "Use this option to keep the original leaf order in the Newick file."
        )
    )

    args = parser.parse_args()

    legend_anchor = None

    if args.legend_anchor is not None:
        legend_anchor = tuple(args.legend_anchor)

    plot_gain_loss_tree(
        tree_file=args.input,
        output=args.output,
        fig_width=args.width,
        fig_height=args.height,
        pie_size=args.pie_size,
        label_size=args.label_size,
        node_text_size=args.text_size,
        branch_width=args.branch_width,
        gain_color=args.gain_color,
        loss_color=args.loss_color,
        slash_color=args.slash_color,
        leaf_label_color=args.leaf_label_color,
        label_bg_color=args.label_bg_color,
        text_bg_color=args.text_bg_color,
        legend_loc=args.legend_loc,
        legend_anchor=legend_anchor,
        show_legend=not args.hide_legend,
        title_text=args.title_text,
        title_size=args.title_size,
        tick_interval=args.tick_interval,
        max_ticks=args.max_ticks,
        no_ladderize=args.no_ladderize,
        leaf_label_gap=args.leaf_label_gap,
        leaf_pie_gap=args.leaf_pie_gap,
        leaf_text_gap=args.leaf_text_gap,
        rename_file=args.rename_file,
        show_branch_length=args.show_branch_length,
        branch_length_size=args.branch_length_size,
        branch_length_color=args.branch_length_color,
        branch_length_bg_color=args.branch_length_bg_color,
        branch_length_offset=args.branch_length_offset
    )


if __name__ == "__main__":
    main()