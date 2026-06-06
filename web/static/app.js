/* Markify — app.js */

const dropZone      = document.getElementById('dropZone');
const fileInput     = document.getElementById('fileInput');
const queueSection  = document.getElementById('queueSection');
const fileQueue     = document.getElementById('fileQueue');
const convertAllBtn = document.getElementById('convertAllBtn');
const downloadZipBtn= document.getElementById('downloadZipBtn');
const previewSection= document.getElementById('previewSection');
const previewContent= document.getElementById('previewContent');
const previewSkeleton=document.getElementById('previewSkeleton');
const rawContent    = document.getElementById('rawContent');
const toggleRawBtn  = document.getElementById('toggleRawBtn');
const copyBtn       = document.getElementById('copyBtn');
const downloadMdBtn = document.getElementById('downloadMdBtn');
const toast         = document.getElementById('toast');

let files        = [];
let jobs         = {};   // filename -> { status, job_id, markdown, error }
let currentJobId = null;
let showRaw      = false;

// ── Drop zone ────────────────────────────────────────────
dropZone.addEventListener('dragover', e => {
  e.preventDefault();
  dropZone.classList.add('dragover');
});
dropZone.addEventListener('dragleave', e => {
  if (!dropZone.contains(e.relatedTarget)) dropZone.classList.remove('dragover');
});
dropZone.addEventListener('drop', e => {
  e.preventDefault();
  dropZone.classList.remove('dragover');
  addFiles([...e.dataTransfer.files]);
});
dropZone.addEventListener('click', () => fileInput.click());
dropZone.addEventListener('keydown', e => {
  if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); fileInput.click(); }
});
fileInput.addEventListener('change', () => addFiles([...fileInput.files]));

// ── File management ──────────────────────────────────────
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
    const ext  = f.name.split('.').pop().toLowerCase();
    const job  = jobs[f.name] || {};
    const { statusHtml, statusClass } = getStatusDisplay(job.status);

    return `<div
      class="queue-item"
      role="listitem"
      tabindex="0"
      onclick="selectFile('${escHtml(f.name)}')"
      onkeydown="if(event.key==='Enter')selectFile('${escHtml(f.name)}')"
      aria-label="${escHtml(f.name)}, ${job.status || 'pending'}"
    >
      <span class="badge badge-${ext}" aria-hidden="true">${ext.toUpperCase()}</span>
      <span class="filename">${escHtml(f.name)}</span>
      <span class="status ${statusClass}" aria-live="polite">${statusHtml}</span>
    </div>`;
  }).join('');
}

function getStatusDisplay(status) {
  switch (status) {
    case 'converting':
      return { statusHtml: '<span class="spinner" aria-hidden="true"></span> Converting…', statusClass: 'status-converting' };
    case 'done':
      return { statusHtml: iconCheck() + ' Done',  statusClass: 'status-done' };
    case 'error':
      return { statusHtml: iconX()     + ' Error', statusClass: 'status-error' };
    default:
      return { statusHtml: 'Pending', statusClass: '' };
  }
}

function iconCheck() {
  return `<svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true"><path d="M2 6l3 3 5-5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
}
function iconX() {
  return `<svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true"><path d="M3 3l6 6M9 3l-6 6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>`;
}

function escHtml(str) {
  return str.replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function selectFile(name) {
  const job = jobs[name];
  if (!job || job.status !== 'done') return;
  currentJobId = job.job_id;
  showMarkdown(job.markdown);
  downloadMdBtn.onclick = () => window.open(`/download/${job.job_id}`);
}

// ── Conversion ───────────────────────────────────────────
convertAllBtn.addEventListener('click', async () => {
  convertAllBtn.disabled = true;
  for (const file of files) {
    if (jobs[file.name]?.status === 'done') continue;
    jobs[file.name] = { status: 'converting' };
    renderQueue();
    showSkeleton();

    const form = new FormData();
    form.append('file', file);
    try {
      const res  = await fetch('/convert', { method: 'POST', body: form });
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
        hideSkeleton();
      }
    } catch (e) {
      jobs[file.name] = { status: 'error', error: e.message };
      hideSkeleton();
    }
    renderQueue();
  }
  convertAllBtn.disabled = false;
  const anyDone = Object.values(jobs).some(j => j.status === 'done');
  if (anyDone) downloadZipBtn.classList.remove('hidden');
});

downloadZipBtn.addEventListener('click', () => {
  if (currentJobId) window.open(`/download/${currentJobId}/zip`);
});

// ── Skeleton ──────────────────────────────────────────────
function showSkeleton() {
  previewSection.classList.remove('hidden');
  previewSkeleton.classList.remove('hidden');
  previewContent.classList.add('hidden');
  rawContent.classList.add('hidden');
}

function hideSkeleton() {
  previewSkeleton.classList.add('hidden');
}

// ── Markdown display ─────────────────────────────────────
function showMarkdown(md) {
  hideSkeleton();
  previewSection.classList.remove('hidden');
  rawContent.value = md;
  if (showRaw) {
    previewContent.classList.add('hidden');
    rawContent.classList.remove('hidden');
  } else {
    previewContent.classList.remove('hidden');
    rawContent.classList.add('hidden');
    renderPreview(md);
  }
}

function renderPreview(md) {
  let html = md
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/^#### (.+)$/gm,'<h4>$1</h4>')
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm,  '<h2>$1</h2>')
    .replace(/^# (.+)$/gm,   '<h1>$1</h1>')
    .replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>')
    .replace(/_(.+?)_/g,      '<em>$1</em>')
    .replace(/^&gt; (.+)$/gm,'<blockquote>$1</blockquote>')
    .replace(/`(.+?)`/g,      '<code>$1</code>')
    .replace(/^---$/gm,       '<hr>')
    .replace(/!\[([^\]]*)\]\(([^)]+)\)/g,'<img src="$2" alt="$1" loading="lazy">')
    .replace(/\n\n/g,         '<br><br>');

  // GFM tables
  html = html.replace(/(\|.+\|\n\|[-| :]+\|\n(?:\|.+\|\n?)+)/g, match => {
    const rows  = match.trim().split('\n').filter(r => !r.match(/^\|[-| :]+\|$/));
    const cells = rows.map(r => r.split('|').filter((_,i,a) => i > 0 && i < a.length-1).map(c => c.trim()));
    if (!cells.length) return match;
    const thead = `<tr>${cells[0].map(c=>`<th>${c}</th>`).join('')}</tr>`;
    const tbody = cells.slice(1).map(row=>`<tr>${row.map(c=>`<td>${c}</td>`).join('')}</tr>`).join('');
    return `<table><thead>${thead}</thead><tbody>${tbody}</tbody></table>`;
  });

  previewContent.innerHTML = html;
}

// ── Preview controls ─────────────────────────────────────
toggleRawBtn.addEventListener('click', () => {
  showRaw = !showRaw;
  toggleRawBtn.setAttribute('aria-pressed', String(showRaw));
  toggleRawBtn.querySelector('span') && (toggleRawBtn.querySelector('span').textContent = showRaw ? 'Preview' : 'Raw');

  // Update button text node (after the SVG icon)
  const textNode = [...toggleRawBtn.childNodes].find(n => n.nodeType === 3);
  if (textNode) textNode.textContent = showRaw ? ' Preview' : ' Raw';

  previewContent.classList.toggle('hidden', showRaw);
  rawContent.classList.toggle('hidden', !showRaw);
});

copyBtn.addEventListener('click', async () => {
  if (!rawContent.value) return;
  try {
    await navigator.clipboard.writeText(rawContent.value);
    showToast('Copied to clipboard');
  } catch {
    showToast('Copy failed — try selecting text manually');
  }
});

// ── Toast ────────────────────────────────────────────────
let toastTimer;
function showToast(msg) {
  toast.textContent = msg;
  toast.classList.remove('hidden');
  requestAnimationFrame(() => toast.classList.add('show'));
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.classList.add('hidden'), 200);
  }, 2200);
}
