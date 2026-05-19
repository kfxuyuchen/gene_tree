let renameDict = {};

document.getElementById("treeFile").addEventListener("change", async e => {
  const file = e.target.files[0];
  if (!file) return;
  document.getElementById("newickInput").value = await file.text();
});

document.getElementById("renameFile").addEventListener("change", async e => {
  const file = e.target.files[0];
  if (!file) return;
  renameDict = parseRename(await file.text());
  alert("rename 文件已读取，共 " + Object.keys(renameDict).length + " 条。");
});

document.getElementById("paramsFile").addEventListener("change", async e => {
  const file = e.target.files[0];
  if (!file) return;
  loadParamsJSON(await file.text());
});

function parseRename(text) {
  const dict = {};
  text.split(/\r?\n/).forEach(line => {
    line = line.trim();
    if (!line || line.startsWith("#")) return;
    const m = line.match(/^(\S+)\s+(.+)$/);
    if (m) dict[m[1]] = m[2].trim();
  });
  return dict;
}

function parseGainLoss(name) {
  if (!name) return { gain: 0, loss: 0 };
  const m = name.match(/\+(\d+)\/-(\d+)/);
  return m ? { gain: +m[1], loss: +m[2] } : { gain: 0, loss: 0 };
}

function cleanLabel(name) {
  if (!name) return "";
  return name
    .replace(/\+(\d+)\/-(\d+)/g, "")
    .replace(/<[^>]*>/g, "")
    .trim();
}

function renameLabel(label) {
  return renameDict[label] || label;
}

function parseNewick(s) {
  s = s.trim().replace(/;$/, "");
  let i = 0;

  function skipSpace() {
    while (i < s.length && /\s/.test(s[i])) i++;
  }

  function parseNameLength(node) {
    skipSpace();

    let token = "";
    let quote = null;

    while (i < s.length) {
      const ch = s[i];

      if (quote) {
        token += ch;
        i++;
        if (ch === quote) quote = null;
        continue;
      }

      if (ch === "'" || ch === '"') {
        quote = ch;
        token += ch;
        i++;
        continue;
      }

      if (ch === "," || ch === ")" || ch === "(") break;

      token += ch;
      i++;
    }

    token = token.trim();

    let name = token;
    let branchLength = null;

    const colon = token.lastIndexOf(":");
    if (colon >= 0) {
      name = token.slice(0, colon).trim();
      const bl = parseFloat(token.slice(colon + 1));
      branchLength = Number.isFinite(bl) ? bl : null;
    }

    name = name.replace(/^['"]|['"]$/g, "");

    node.name = name;
    node.branchLength = branchLength;
  }

  function parseSubtree() {
    skipSpace();

    const node = {
      name: "",
      branchLength: null,
      children: [],
      parent: null
    };

    if (s[i] === "(") {
      i++;

      while (true) {
        const child = parseSubtree();
        child.parent = node;
        node.children.push(child);

        skipSpace();

        if (s[i] === ",") {
          i++;
          continue;
        }

        if (s[i] === ")") {
          i++;
          break;
        }

        break;
      }

      parseNameLength(node);
    } else {
      parseNameLength(node);
    }

    return node;
  }

  return parseSubtree();
}

function traverse(node, fn) {
  fn(node);
  if (node.children) node.children.forEach(c => traverse(c, fn));
}

function getTerminals(root) {
  const leaves = [];
  traverse(root, n => {
    if (!n.children || n.children.length === 0) leaves.push(n);
  });
  return leaves;
}

function countLeaves(node) {
  if (!node.children || node.children.length === 0) return 1;
  return node.children.reduce((s, c) => s + countLeaves(c), 0);
}

function ladderize(node) {
  if (!node.children) return;
  node.children.forEach(ladderize);
  node.children.sort((a, b) => countLeaves(b) - countLeaves(a));
}

function computePositions(root) {
  let maxX = 0;

  function setX(node, x) {
    node.xRaw = x;
    maxX = Math.max(maxX, x);

    if (node.children && node.children.length) {
      node.children.forEach(c => {
        const bl = c.branchLength == null ? 1 : c.branchLength;
        setX(c, x + bl);
      });
    }
  }

  setX(root, 0);

  const leaves = getTerminals(root);

  leaves.forEach((leaf, i) => {
    leaf.yRaw = i;
  });

  function setY(node) {
    if (!node.children || node.children.length === 0) return node.yRaw;
    node.yRaw = d3.mean(node.children, setY);
    return node.yRaw;
  }

  setY(root);

  return {
    maxX,
    maxY: leaves.length - 1,
    leaves
  };
}

function makeTicks(maxX, interval) {
  const maxMya = Math.round(maxX);

  if (maxMya <= 0) {
    return [{ x: maxX, label: "0" }];
  }

  let step = interval;

  if (!step || step <= 0) {
    const raw = maxMya / 7;
    const nice = [1, 2, 5, 10, 20, 25, 50, 100, 200, 500, 1000];
    step = nice.find(v => v >= raw) || nice[nice.length - 1];
  }

  const vals = [];

  for (let v = 0; v <= maxMya; v += step) {
    vals.push(v);
  }

  if (!vals.includes(maxMya)) vals.push(maxMya);

  return vals.map(v => ({
    x: maxX - v,
    label: String(v)
  }));
}

function getParams() {
  const val = id => document.getElementById(id).value;
  const num = id => +val(id);
  const bool = id => document.getElementById(id).checked;

  const ax = val("legendAnchorX");
  const ay = val("legendAnchorY");

  return {
    width: num("figWidth"),
    height: num("figHeight"),
    pieSize: num("pieSize"),
    branchWidth: num("branchWidth"),
    labelSize: num("labelSize"),
    textSize: num("textSize"),

    gainColor: val("gainColor"),
    lossColor: val("lossColor"),
    slashColor: val("slashColor"),
    leafLabelColor: val("leafLabelColor"),

    labelBgColor: val("labelBgColor"),
    textBgColor: val("textBgColor"),
    bgOpacity: num("bgOpacity"),
    bgPadding: num("bgPadding"),

    leafLabelGap: num("leafLabelGap"),
    leafPieGap: num("leafPieGap"),
    leafTextGap: num("leafTextGap"),
    tickInterval: val("tickInterval") ? num("tickInterval") : null,

    showBranchLength: bool("showBranchLength"),
    branchLengthSize: num("branchLengthSize"),
    branchLengthOffset: num("branchLengthOffset"),
    branchLengthColor: val("branchLengthColor"),

    showRootMrca: bool("showRootMrca"),
    rootMrcaValue: val("rootMrcaValue"),
    rootMrcaSize: num("rootMrcaSize"),
    rootMrcaOffsetX: num("rootMrcaOffsetX"),
    rootMrcaOffsetY: num("rootMrcaOffsetY"),
    rootMrcaColor: val("rootMrcaColor"),
    rootMrcaBgColor: val("rootMrcaBgColor"),
    rootMrcaBgOpacity: num("rootMrcaBgOpacity"),

    noLadderize: bool("noLadderize"),

    showLegend: bool("showLegend"),
    titleText: val("titleText"),
    legendLoc: val("legendLoc"),

    legendAnchor: ax !== "" && ay !== "" ? { x: +ax, y: +ay } : null
  };
}

function renderTree() {
  const newick = document.getElementById("newickInput").value.trim();

  if (!newick) {
    alert("请先输入或上传 Newick。");
    return;
  }

  let root;

  try {
    root = parseNewick(newick);
  } catch (e) {
    alert("Newick 解析失败：" + e.message);
    return;
  }

  const p = getParams();

  if (!p.noLadderize) ladderize(root);

  const { maxX, maxY, leaves } = computePositions(root);

  const margin = {
    top: 60,
    right: 380,
    bottom: 70,
    left: 65
  };

  const innerW = p.width - margin.left - margin.right;
  const innerH = p.height - margin.top - margin.bottom;

  const xScale = d3.scaleLinear()
    .domain([0, maxX || 1])
    .range([0, innerW]);

  const yScale = d3.scaleLinear()
    .domain([-1, Math.max(maxY, 1) + 1])
    .range([0, innerH]);

  const svg = d3.select("#plot")
    .attr("width", p.width)
    .attr("height", p.height)
    .attr("viewBox", `0 0 ${p.width} ${p.height}`);

  svg.selectAll("*").remove();

  const g = svg.append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);

  const sx = n => xScale(n.xRaw);
  const sy = n => yScale(n.yRaw);

  const labelX = xScale(maxX) + maxX * p.leafLabelGap * 8;

  const maxLabelLen = d3.max(leaves, d => renameLabel(cleanLabel(d.name)).length) || 8;
  const labelWidthEst = maxLabelLen * p.labelSize * 0.15;

  const leafPieX = labelX + labelWidthEst + maxX * p.leafPieGap * 8;
  const leafTextX = leafPieX + maxX * p.leafTextGap * 8;

  drawBranches(g, root, sx, sy, p);

  if (p.showRootMrca && p.rootMrcaValue) {
    addRootMrcaText(
      g,
      sx(root) + p.rootMrcaOffsetX,
      sy(root) + p.rootMrcaOffsetY,
      p
    );
  }

  let internalIndex = 0;

  traverse(root, node => {
    if (!node.children || node.children.length === 0) return;

    const { gain, loss } = parseGainLoss(node.name);
    if (gain + loss <= 0) return;

    addPie(g, sx(node), sy(node), gain, loss, p);

    const offsetList = [
      [0, -14],
      [0, -24],
      [8, -18],
      [-8, -18],
      [12, -24],
      [-12, -24]
    ];

    const off = offsetList[internalIndex % offsetList.length];

    addGainLossText(
      g,
      sx(node) + off[0],
      sy(node) + off[1],
      gain,
      loss,
      p,
      "middle"
    );

    internalIndex++;
  });

  leaves.forEach(leaf => {
    const y = sy(leaf);
    const label = renameLabel(cleanLabel(leaf.name));
    const { gain, loss } = parseGainLoss(leaf.name);

    const leafText = g.append("text")
      .attr("x", labelX)
      .attr("y", y)
      .attr("dominant-baseline", "middle")
      .attr("font-size", p.labelSize)
      .attr("font-style", "italic")
      .attr("fill", p.leafLabelColor)
      .text(label);

    addTextBackground(leafText, p.labelBgColor, p.bgOpacity, p.bgPadding);

    if (gain + loss > 0) {
      addPie(g, leafPieX, y, gain, loss, p);
      addGainLossText(g, leafTextX, y, gain, loss, p, "start");
    }
  });

  drawAxis(g, maxX, xScale, innerH, p);
  if (p.showLegend) drawLegend(svg, p);
}

function drawBranches(g, root, sx, sy, p) {
  traverse(root, node => {
    if (!node.children || node.children.length === 0) return;

    const childYs = node.children.map(sy);

    g.append("line")
      .attr("x1", sx(node))
      .attr("x2", sx(node))
      .attr("y1", d3.min(childYs))
      .attr("y2", d3.max(childYs))
      .attr("stroke", "black")
      .attr("stroke-width", p.branchWidth);

    node.children.forEach(child => {
      g.append("line")
        .attr("x1", sx(node))
        .attr("x2", sx(child))
        .attr("y1", sy(child))
        .attr("y2", sy(child))
        .attr("stroke", "black")
        .attr("stroke-width", p.branchWidth);

      if (p.showBranchLength && child.branchLength != null) {
        const txt = g.append("text")
          .attr("x", (sx(node) + sx(child)) / 2)
          .attr("y", sy(child) - p.branchLengthOffset)
          .attr("text-anchor", "middle")
          .attr("font-size", p.branchLengthSize)
          .attr("fill", p.branchLengthColor)
          .text(child.branchLength.toFixed(2));

        addTextBackground(txt, p.textBgColor, p.bgOpacity, p.bgPadding);
      }
    });
  });
}

function addPie(g, x, y, gain, loss, p) {
  const total = gain + loss;
  if (total <= 0) return;

  const r = p.pieSize / 2;

  const group = g.append("g")
    .attr("transform", `translate(${x},${y})`);

  group.append("circle")
    .attr("r", r)
    .attr("fill", p.lossColor)
    .attr("stroke", "white")
    .attr("stroke-width", 0.7);

  const arc = d3.arc()
    .innerRadius(0)
    .outerRadius(r)
    .startAngle(0)
    .endAngle(2 * Math.PI * gain / total);

  group.append("path")
    .attr("d", arc)
    .attr("fill", p.gainColor)
    .attr("stroke", "white")
    .attr("stroke-width", 0.7);
}

function addGainLossText(g, x, y, gain, loss, p, anchor) {
  const text = g.append("text")
    .attr("x", x)
    .attr("y", y)
    .attr("font-size", p.textSize)
    .attr("text-anchor", anchor)
    .attr("dominant-baseline", "middle");

  text.append("tspan")
    .attr("fill", p.gainColor)
    .text("+" + gain);

  text.append("tspan")
    .attr("fill", p.slashColor)
    .text("/");

  text.append("tspan")
    .attr("fill", p.lossColor)
    .text("-" + loss);

  addTextBackground(text, p.textBgColor, p.bgOpacity, p.bgPadding);

  return text;
}

function addRootMrcaText(g, x, y, p) {
  const text = g.append("text")
    .attr("x", x)
    .attr("y", y)
    .attr("text-anchor", "middle")
    .attr("dominant-baseline", "middle")
    .attr("font-size", p.rootMrcaSize)
    .attr("fill", p.rootMrcaColor);

  text.append("tspan")
    .attr("x", x)
    .attr("dy", "0em")
    .text("MRCA");

  text.append("tspan")
    .attr("x", x)
    .attr("dy", "1.15em")
    .text(p.rootMrcaValue);

  addTextBackground(
    text,
    p.rootMrcaBgColor,
    p.rootMrcaBgOpacity,
    p.bgPadding
  );

  return text;
}

function addTextBackground(selection, color, opacity, padding) {
  selection.each(function () {
    const node = this;
    let bbox;

    try {
      bbox = node.getBBox();
    } catch (e) {
      return;
    }

    d3.select(node.parentNode)
      .insert("rect", () => node)
      .attr("x", bbox.x - padding)
      .attr("y", bbox.y - padding)
      .attr("width", bbox.width + padding * 2)
      .attr("height", bbox.height + padding * 2)
      .attr("rx", 3)
      .attr("ry", 3)
      .attr("fill", color)
      .attr("opacity", opacity)
      .attr("stroke", "none");
  });
}

function drawAxis(g, maxX, xScale, innerH, p) {
  const axisY = innerH + 22;

  g.append("line")
    .attr("x1", 0)
    .attr("x2", xScale(maxX))
    .attr("y1", axisY)
    .attr("y2", axisY)
    .attr("stroke", "black");

  makeTicks(maxX, p.tickInterval).forEach(t => {
    const x = xScale(t.x);

    g.append("line")
      .attr("x1", x)
      .attr("x2", x)
      .attr("y1", axisY)
      .attr("y2", axisY + 5)
      .attr("stroke", "black");

    g.append("text")
      .attr("x", x)
      .attr("y", axisY + 21)
      .attr("text-anchor", "middle")
      .attr("font-size", 11)
      .text(t.label);
  });

  g.append("text")
    .attr("x", xScale(maxX) / 2)
    .attr("y", axisY + 45)
    .attr("text-anchor", "middle")
    .attr("font-size", 13)
    .text("MYA");
}

function drawLegend(svg, p) {
  let x = 70;
  let y = 38;

  if (p.legendAnchor) {
    x = p.legendAnchor.x * p.width;
    y = p.legendAnchor.y * p.height;
  } else {
    if (p.legendLoc.includes("right")) x = p.width - 220;
    if (p.legendLoc.includes("lower")) y = p.height - 95;
  }

  const lg = svg.append("g")
    .attr("transform", `translate(${x},${y})`);

  if (p.titleText) {
    lg.append("text")
      .attr("x", 0)
      .attr("y", -14)
      .attr("font-size", 14)
      .attr("font-weight", "bold")
      .text(p.titleText);
  }

  lg.append("rect")
    .attr("x", 0)
    .attr("y", 0)
    .attr("width", 14)
    .attr("height", 14)
    .attr("fill", p.gainColor);

  lg.append("text")
    .attr("x", 22)
    .attr("y", 12)
    .attr("font-size", 13)
    .text("Expansion");

  lg.append("rect")
    .attr("x", 0)
    .attr("y", 24)
    .attr("width", 14)
    .attr("height", 14)
    .attr("fill", p.lossColor);

  lg.append("text")
    .attr("x", 22)
    .attr("y", 36)
    .attr("font-size", 13)
    .text("Contraction");
}

function getSVGSource() {
  const svg = document.getElementById("plot");
  const serializer = new XMLSerializer();
  let source = serializer.serializeToString(svg);

  if (!source.match(/^<svg[^>]+xmlns=/)) {
    source = source.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"');
  }

  return source;
}

function downloadSVG() {
  const source = getSVGSource();
  const blob = new Blob([source], { type: "image/svg+xml;charset=utf-8" });

  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "gene_family_gain_loss_tree.svg";
  a.click();
  URL.revokeObjectURL(a.href);
}

function svgToCanvas(callback) {
  const svg = document.getElementById("plot");
  const source = getSVGSource();

  const blob = new Blob([source], { type: "image/svg+xml;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const img = new Image();

  img.onload = function () {
    const canvas = document.createElement("canvas");
    canvas.width = svg.width.baseVal.value;
    canvas.height = svg.height.baseVal.value;

    const ctx = canvas.getContext("2d");

    ctx.fillStyle = "white";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(img, 0, 0);

    URL.revokeObjectURL(url);

    callback(canvas);
  };

  img.src = url;
}

function downloadPNG() {
  svgToCanvas(canvas => {
    canvas.toBlob(blob => {
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = "gene_family_gain_loss_tree.png";
      a.click();
      URL.revokeObjectURL(a.href);
    });
  });
}

function downloadPDF() {
  svgToCanvas(canvas => {
    const imgData = canvas.toDataURL("image/png");
    const orientation = canvas.width >= canvas.height ? "landscape" : "portrait";
    const { jsPDF } = window.jspdf;

    const pdf = new jsPDF({
      orientation,
      unit: "pt",
      format: [canvas.width, canvas.height]
    });

    pdf.addImage(imgData, "PNG", 0, 0, canvas.width, canvas.height);
    pdf.save("gene_family_gain_loss_tree.pdf");
  });
}

function saveParamsJSON() {
  const data = {
    version: "2.1",
    params: getParams(),
    renameDict,
    newick: document.getElementById("newickInput").value
  };

  const blob = new Blob(
    [JSON.stringify(data, null, 2)],
    { type: "application/json;charset=utf-8" }
  );

  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "tree_plot_params.json";
  a.click();
  URL.revokeObjectURL(a.href);
}

function loadParamsJSON(text) {
  let data;

  try {
    data = JSON.parse(text);
  } catch (e) {
    alert("JSON 文件解析失败。");
    return;
  }

  if (data.newick) {
    document.getElementById("newickInput").value = data.newick;
  }

  if (data.renameDict) {
    renameDict = data.renameDict;
  }

  if (data.params) {
    setParams(data.params);
  }

  renderTree();
}

function setParams(p) {
  const setVal = (id, value) => {
    const el = document.getElementById(id);
    if (!el || value === undefined || value === null) return;
    el.value = value;
  };

  const setBool = (id, value) => {
    const el = document.getElementById(id);
    if (!el || value === undefined || value === null) return;
    el.checked = !!value;
  };

  setVal("figWidth", p.width);
  setVal("figHeight", p.height);
  setVal("pieSize", p.pieSize);
  setVal("branchWidth", p.branchWidth);
  setVal("labelSize", p.labelSize);
  setVal("textSize", p.textSize);

  setVal("gainColor", p.gainColor);
  setVal("lossColor", p.lossColor);
  setVal("slashColor", p.slashColor);
  setVal("leafLabelColor", p.leafLabelColor);

  setVal("labelBgColor", p.labelBgColor);
  setVal("textBgColor", p.textBgColor);
  setVal("bgOpacity", p.bgOpacity);
  setVal("bgPadding", p.bgPadding);

  setVal("leafLabelGap", p.leafLabelGap);
  setVal("leafPieGap", p.leafPieGap);
  setVal("leafTextGap", p.leafTextGap);
  setVal("tickInterval", p.tickInterval);

  setBool("showBranchLength", p.showBranchLength);
  setVal("branchLengthSize", p.branchLengthSize);
  setVal("branchLengthOffset", p.branchLengthOffset);
  setVal("branchLengthColor", p.branchLengthColor);

  setBool("showRootMrca", p.showRootMrca);
  setVal("rootMrcaValue", p.rootMrcaValue);
  setVal("rootMrcaSize", p.rootMrcaSize);
  setVal("rootMrcaOffsetX", p.rootMrcaOffsetX);
  setVal("rootMrcaOffsetY", p.rootMrcaOffsetY);
  setVal("rootMrcaColor", p.rootMrcaColor);
  setVal("rootMrcaBgColor", p.rootMrcaBgColor);
  setVal("rootMrcaBgOpacity", p.rootMrcaBgOpacity);

  setBool("noLadderize", p.noLadderize);

  setBool("showLegend", p.showLegend);
  setVal("titleText", p.titleText);
  setVal("legendLoc", p.legendLoc);

  if (p.legendAnchor) {
    setVal("legendAnchorX", p.legendAnchor.x);
    setVal("legendAnchorY", p.legendAnchor.y);
  } else {
    setVal("legendAnchorX", "");
    setVal("legendAnchorY", "");
  }
}

function loadExample() {
  const example = "((Athali<17>+2094/-1990:20,Atrich+1362/-3284:20)<33>+493/-731:30,(Osati+900/-700:25,Zmaya+1200/-600:25)<44>+300/-500:25)<root>+100/-80;";

  document.getElementById("newickInput").value = example;

  renameDict = {
    Athali: "Arabidopsis thaliana",
    Atrich: "Amborella trichopoda",
    Osati: "Oryza sativa japonica",
    Zmaya: "Zea mays"
  };

  document.getElementById("showRootMrca").checked = true;
  document.getElementById("rootMrcaValue").value = "50";

  renderTree();
}

loadExample();
