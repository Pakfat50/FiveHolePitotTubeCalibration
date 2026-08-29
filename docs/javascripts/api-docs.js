(() => {
  const labels = new Map([
    ["対応要求:", "requirements"],
    ["設計根拠:", "rationale"],
    ["検証根拠:", "rationale"],
    ["Test:", "test"],
    ["Details:", "details"],
    ["Verification rationale:", "rationale"],
    ["See Also:", "see-also"],
    ["概要:", "overview"],
    ["値:", "overview"]
  ]);

  const decorate = () => {
    document.querySelectorAll(".doc.doc-object .doc-contents p").forEach((paragraph) => {
      if (paragraph.dataset.apiDecorated === "true") return;
      paragraph.dataset.apiDecorated = "true";

      const walker = document.createTreeWalker(paragraph, NodeFilter.SHOW_TEXT);
      const nodes = [];
      while (walker.nextNode()) nodes.push(walker.currentNode);

      nodes.forEach((node) => {
        const text = node.nodeValue;
        const pattern = /(対応要求:|設計根拠:|検証根拠:|Test:|Details:|Verification rationale:|See Also:|概要:|値:)/g;
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
