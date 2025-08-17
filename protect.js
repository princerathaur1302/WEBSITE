// Weak, client-side only. Don't rely on this for real protection.
(function () {
  // Disable right-click
  document.addEventListener('contextmenu', e => e.preventDefault());

  // Block common save/inspect keys
  document.addEventListener('keydown', e => {
    const k = e.key.toLowerCase();
    if ((e.ctrlKey && (k === 's' || k === 'u' || k === 'p')) || // Ctrl+S, Ctrl+U, Ctrl+P
        (e.ctrlKey && e.shiftKey && (k === 'i' || k === 'c' || k === 'j')) || // DevTools
        k === 'f12') {
      e.preventDefault();
      e.stopPropagation();
    }
  });

  // Attempt to prevent drag-save of images
  document.querySelectorAll('img, video').forEach(el => {
    el.setAttribute('draggable', 'false');
  });

  // Stop selection on text content
  document.documentElement.style.userSelect = 'none';
  document.documentElement.style.webkitUserSelect = 'none';
})();