(() => {
  const applyContrast = (root = document) => {
    root.querySelectorAll(".mermaid svg").forEach((svg) => {
      svg.querySelectorAll("text, .nodeLabel, .nodeLabel *, .label, foreignObject div, foreignObject span")
        .forEach((element) => {
          element.style.setProperty("color", "#111827", "important");
          element.style.setProperty("fill", "#111827", "important");
        });

      svg.querySelectorAll(".edgePath path, .flowchart-link")
        .forEach((element) => {
          element.style.setProperty("stroke", "#374151", "important");
        });
    });
  };

  const observer = new MutationObserver(() => applyContrast());
  observer.observe(document.documentElement, { childList: true, subtree: true });

  document.addEventListener("DOMContentLoaded", () => applyContrast());
  if (window.document$) {
    document$.subscribe(() => applyContrast());
  }
})();
