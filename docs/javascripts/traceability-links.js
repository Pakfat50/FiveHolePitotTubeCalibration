function linkTraceabilityIds() {
  "use strict";

  const idPattern = /\b(?:REQ-[A-Z0-9-]+|TEST-(?:UNIT|UC)-[A-Z0-9-]+|UC-[0-9]{2})\b/g;
  const root = document.querySelector(".md-content__inner");
  if (!root) return;

  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  const nodes = [];
  while (walker.nextNode()) nodes.push(walker.currentNode);

  nodes.forEach((node) => {
    const parent = node.parentElement;
    if (!parent || parent.closest("a, code, pre, script, style")) return;
    const text = node.nodeValue;
    if (!idPattern.test(text)) {
      idPattern.lastIndex = 0;
      return;
    }
    idPattern.lastIndex = 0;
    const fragment = document.createDocumentFragment();
    let offset = 0;
    text.replace(idPattern, (id, position) => {
      fragment.append(document.createTextNode(text.slice(offset, position)));
      const link = document.createElement("a");
      link.textContent = id;
      link.href = id.startsWith("REQ-")
        ? `../pitot_calibration_gui_spec/#${id.toLowerCase()}`
        : id.startsWith("TEST-")
          ? `../test-specification/#${id.toLowerCase()}`
          : `../architecture_design/#${id.toLowerCase()}`;
      fragment.append(link);
      offset = position + id.length;
      return id;
    });
    fragment.append(document.createTextNode(text.slice(offset)));
    node.parentNode.replaceChild(fragment, node);
  });
}

if (typeof document$ !== "undefined") {
  document$.subscribe(linkTraceabilityIds);
} else {
  document.addEventListener("DOMContentLoaded", linkTraceabilityIds);
}
