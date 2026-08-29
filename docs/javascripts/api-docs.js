(() => {
  const labels = new Map([
    ["引数:", "parameters"],
    ["戻り値:", "returns"],
    ["対応要求:", "requirements"],
    ["設計根拠:", "rationale"],
    ["検証根拠:", "rationale"],
    ["概要:", "overview"],
    ["値:", "overview"]
  ]);

  const convertParameters = (paragraph) => {
    const text = paragraph.textContent.replace(/\s+/g, " ").trim();
    if (!text.startsWith("引数:")) return false;

    const body = text.slice("引数:".length).trim();
    const matches = [...body.matchAll(/(?:^|\s)([A-Za-z_]\w*):\s*(.*?)(?=\s+[A-Za-z_]\w*:\s*|$)/gs)];
    if (!matches.length) return false;

    const label = document.createElement("span");
    label.className = "doc-section-label";
    label.dataset.section = "parameters";
    label.textContent = "引数";

    const table = document.createElement("table");
    table.className = "api-parameters";
    table.innerHTML = "<thead><tr><th>引数名</th><th>説明</th></tr></thead>";
    const tbody = document.createElement("tbody");

    matches.forEach((match) => {
      const row = document.createElement("tr");
      const name = document.createElement("code");
      name.textContent = match[1];
      const nameCell = document.createElement("td");
      nameCell.appendChild(name);
      const descriptionCell = document.createElement("td");
      descriptionCell.textContent = match[2].trim();
      row.append(nameCell, descriptionCell);
      tbody.appendChild(row);
    });

    table.appendChild(tbody);
    paragraph.replaceChildren(label, table);
    return true;
  };

  const decorate = () => {
    document.querySelectorAll(".doc.doc-object .doc-contents p").forEach((paragraph) => {
      if (paragraph.dataset.apiDecorated === "true") return;
      paragraph.dataset.apiDecorated = "true";
      if (convertParameters(paragraph)) return;

      const walker = document.createTreeWalker(paragraph, NodeFilter.SHOW_TEXT);
      const nodes = [];
      while (walker.nextNode()) nodes.push(walker.currentNode);

      nodes.forEach((node) => {
        const text = node.nodeValue;
        const pattern = /(引数:|戻り値:|対応要求:|設計根拠:|検証根拠:|概要:|値:)/g;
        if (!pattern.test(text)) return;
        pattern.lastIndex = 0;

        const fragment = document.createDocumentFragment();
        let last = 0;
        text.replace(pattern, (match, _value, offset) => {
          fragment.appendChild(document.createTextNode(text.slice(last, offset)));
          const label = document.createElement("span");
          label.className = "doc-section-label";
          label.dataset.section = labels.get(match);
          label.textContent = match.slice(0, -1);
          fragment.appendChild(label);
          last = offset + match.length;
          return match;
        });
        fragment.appendChild(document.createTextNode(text.slice(last)));
        node.parentNode.replaceChild(fragment, node);
      });
    });
  };

  document.addEventListener("DOMContentLoaded", decorate);
  if (window.document$) document$.subscribe(decorate);
})();
