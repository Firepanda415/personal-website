document.querySelectorAll('[data-copy]').forEach(button => {
  button.addEventListener('click', async () => {
    const bio = document.getElementById(button.dataset.copy);
    const status = document.getElementById('copy-status');
    try {
      await navigator.clipboard.writeText(bio.textContent);
      button.textContent = 'Bio copied ✓';
      status.textContent = 'Biography copied to clipboard.';
    } catch {
      const range = document.createRange();
      range.selectNodeContents(bio);
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
      status.textContent = 'Automatic copying is unavailable. The biography is selected. Use your keyboard copy command.';
      button.textContent = 'Bio selected — press Ctrl/Cmd+C';
    }
  });
});
