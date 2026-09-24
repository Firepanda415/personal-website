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

const explainerDialog = document.getElementById('explainer-dialog');
if (explainerDialog && explainerDialog.showModal) {
  const video = explainerDialog.querySelector('video');
  document.querySelectorAll('[data-explainer]').forEach(link => {
    link.addEventListener('click', event => {
      event.preventDefault();
      const track = document.createElement('track');
      Object.assign(track, {kind: 'captions', srclang: 'en', label: 'English', src: link.dataset.captions});
      video.replaceChildren(track);
      video.src = link.dataset.explainer;
      explainerDialog.querySelector('.explainer-title').textContent = link.dataset.title;
      explainerDialog.showModal();
      video.play().catch(() => {});
    });
  });
  explainerDialog.addEventListener('click', event => { if (event.target === explainerDialog) explainerDialog.close(); });
  explainerDialog.addEventListener('close', () => { video.pause(); video.removeAttribute('src'); video.replaceChildren(); video.load(); });
}
