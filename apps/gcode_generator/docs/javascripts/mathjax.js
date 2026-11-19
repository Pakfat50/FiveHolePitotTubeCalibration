window.MathJax = {
  tex: {
    inlineMath: [["\\(", "\\)"]],
    displayMath: [["\\[", "\\]"]]
  },
  options: {
    processHtmlClass: "arithmatex",
    ignoreHtmlClass: ".*"
  }
};

function typesetDocumentationMath() {
  if (window.MathJax && window.MathJax.typesetPromise) {
    window.MathJax.typesetPromise();
  }
}

if (typeof document$ !== "undefined") {
  document$.subscribe(() => {
    window.setTimeout(typesetDocumentationMath, 0);
  });
} else {
  document.addEventListener("DOMContentLoaded", typesetDocumentationMath);
}
