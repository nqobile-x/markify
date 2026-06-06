const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const queueSection = document.getElementById('queueSection');
const fileQueue = document.getElementById('fileQueue');
const convertAllBtn = document.getElementById('convertAllBtn');
const downloadZipBtn = document.getElementById('downloadZipBtn');
const previewSection = document.getElementById('previewSection');
const previewContent = document.getElementById('previewContent');
const rawContent = document.getElementById('rawContent');
const toggleRawBtn = document.getElementById('toggleRawBtn');
const copyBtn = document.getElementById('copyBtn');
const downloadMdBtn = document.getElementById('downloadMdBtn');

let files = [];
let jobs = {};
let currentJobId = null;
let showRaw = false;

dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', e => {
  e.preventDefault();
  dropZone.classList.remove('dragover');
  addFiles([...e.dataTransfer.files]);
});
fileInput.addEventListener('change', () => addFiles([...fileInput.files]));

function addFiles(newFiles) {
  newFiles.forEach(f => {
    if (!files.find(x => x.name === f.name)) files.push(f);
  });
  renderQueue();
}

function renderQueue() {
  if (!files.length) { queueSection.classList.add('hidden'); return; }
  queueSection.classList.remove('hidden');
  fileQueue.innerHTML = files.map(f => {
    const ext = f.name.split('.').pop().toLowerCase();
    const job = jobs[f.name] || {};
    const statusText = job.status === 'done' ? '✓ Done'
      : job.status === 'error' ? '✗ Error'
      : job.status === 'converting' ? '⏳ Converting…'
      : 'Pending';
    const statusClass = job.status === 'done' ? 'status-done' : job.status === 'error' ? 'status-error' : '';
    return `<div class="queue-item" onclick="selectFile('${f.name}')" style="cursor:pointer">
      <span class="badge badge-${ext}">${ext.toUpperCase()}</span>
      <span class="filename">${f.name}</span>
      <span class="status ${statusClass}">${statusText}</span>
    </div>`;
  }).join('');
}

function selectFile(name) {
  const job = jobs[name];
  if (!job || job.status !== 'done') return;
  currentJobId = job.job_id;
  showMarkdown(job.markdown);
  downloadMdBtn.onclick = () => window.open(`/download/${job.job_id}`);
}

convertAllBtn.addEventListener('click', async () => {
  for (const file of files) {
    if (jobs[file.name]?.status === 'done') continue;
    jobs[file.name] = { status: 'converting' };
    renderQueue();
    const form = new FormData();
    form.append('file', file);
    try {
      const res = await fetch('/convert', { method: 'POST', body: form });
      const data = await res.json();
      if (data.status === 'done') {
        jobs[file.name] = { status: 'done', job_id: data.job_id, markdown: data.markdown };
        if (!currentJobId) {
          currentJobId = data.job_id;
          showMarkdown(data.markdown);
          downloadMdBtn.onclick = () => window.open(`/download/${data.job_id}`);
        }
      } else {
        jobs[file.name] = { status: 'error', error: data.error };
      }
    } catch (e) {
      jobs[file.name] = { status: 'error', error: e.message };
    }
    renderQueue();
  }
  const anyDone = Object.values(jobs).some(j => j.status === 'done');
  if (anyDone) downloadZipBtn.classList.remove('hidden');
});

downloadZipBtn.addEventListener('click', () => {
  if (currentJobId) window.open(`/download/${currentJobId}/zip`);
});

function showMarkdown(md) {
  previewSection.classList.remove('hidden');
  rawContent.value = md;
  renderPreview(md);
}

function renderPreview(md) {
  let html = md
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/^#### (.+)$/gm, '<h4>$1</h4>')
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/_(.+?)_/g, '<em>$1</em>')
    .replace(/^&gt; (.+)$/gm, '<blockquote>$1</blockquote>')
    .replace(/`(.+?)`/g, '<code>$1</code>')
    .replace(/^---$/gm, '<hr>')
    .replace(/\n\n/g, '<br><br>');

  html = html.replace(/(\|.+\|\n\|[-| :]+\|\n(?:\|.+\|\n?)+)/g, match => {
    const rows = match.trim().split('\n').filter(r => !r.match(/^\|[-| :]+\|$/));
    const cells = rows.map(r => r.split('|').filter((_, i, a) => i > 0 && i < a.length - 1).map(c => c.trim()));
    if (!cells.length) return match;
    const thead = `<tr>${cells[0].map(c => `<th>${c}</th>`).join('')}</tr>`;
    const tbody = cells.slice(1).map(row => `<tr>${row.map(c => `<td>${c}</td>`).join('')}</tr>`).join('');
    return `<table><thead>${thead}</thead><tbody>${tbody}</tbody></table>`;
  });

  previewContent.innerHTML = html;
}

toggleRawBtn.addEventListener('click', () => {
  showRaw = !showRaw;
  toggleRawBtn.textContent = showRaw ? 'Preview' : 'Raw Markdown';
  previewContent.classList.toggle('hidden', showRaw);
  rawContent.classList.toggle('hidden', !showRaw);
});

copyBtn.addEventListener('click', () => navigator.clipboard.writeText(rawContent.value));
