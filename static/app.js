let links = [];
let editingId = null;

const STATUS_LABEL = {live:'Live', progress:'In progress', idea:'Idea / planned'};
const STATUS_CLASS = {live:'status-live', progress:'status-progress', idea:'status-idea'};

async function apiFetch(url, options){
  const res = await fetch(url, options);
  if(res.status === 401){
    window.location.href = '/';
    throw new Error('Unauthorised');
  }
  return res;
}

async function loadLinks(){
  const res = await apiFetch('/api/links');
  links = await res.json();
  render();
}

function render(){
  const content = document.getElementById('content');
  const q = document.getElementById('search').value.trim().toLowerCase();
  const filtered = links.filter(l =>
    !q || l.name.toLowerCase().includes(q) || l.category.toLowerCase().includes(q) || l.url.toLowerCase().includes(q)
  );

  if(links.length === 0){
    content.innerHTML = `<div class="empty">
      <p style="font-size:14px;color:var(--text);font-weight:500;">No systems yet</p>
      <p>Add your first one to start building the hub.</p>
    </div>`;
    return;
  }
  if(filtered.length === 0){
    content.innerHTML = `<div class="empty"><p>No matches for that search.</p></div>`;
    return;
  }

  const categories = {};
  filtered.forEach(l => {
    const c = l.category || 'Uncategorised';
    if(!categories[c]) categories[c] = [];
    categories[c].push(l);
  });

  content.innerHTML = Object.keys(categories).sort().map(cat => `
    <div class="section">
      <div class="section-head">
        <h2>${escapeHtml(cat)}</h2>
        <div class="line"></div>
        <span class="tag">${categories[cat].length}</span>
      </div>
      <div class="grid">
        ${categories[cat].map(cardHtml).join('')}
      </div>
    </div>
  `).join('');

  updateCategoryList();
}

function cardHtml(l){
  return `
    <div class="card" onclick="openLinkSafe(event, '${l.url.replace(/'/g,"\\'")}')">
      <div class="card-top">
        <h3>${escapeHtml(l.name)}</h3>
        <div class="status-dot ${STATUS_CLASS[l.status] || 'status-idea'}"></div>
      </div>
      <p class="url">${escapeHtml(l.url)}</p>
      <div class="card-foot">
        <span class="status-label">${STATUS_LABEL[l.status] || 'Idea / planned'}</span>
        <div class="card-actions">
          <button class="icon-btn" onclick="event.stopPropagation(); openModal(${l.id})" aria-label="Edit">&#9998;</button>
        </div>
      </div>
    </div>
  `;
}

function openLinkSafe(e, url){
  if(!url) return;
  window.open(url, '_blank');
}

function updateCategoryList(){
  const set = new Set(links.map(l => l.category).filter(Boolean));
  document.getElementById('cat-list').innerHTML =
    Array.from(set).map(c => `<option value="${escapeHtml(c)}">`).join('');
}

function openModal(id){
  editingId = id || null;
  const l = id ? links.find(x => x.id === id) : null;
  document.getElementById('modal-title').textContent = l ? 'Edit system' : 'Add system';
  document.getElementById('f-name').value = l ? l.name : '';
  document.getElementById('f-url').value = l ? l.url : '';
  document.getElementById('f-category').value = l ? l.category : '';
  document.getElementById('f-status').value = l ? l.status : 'live';
  document.getElementById('delete-btn').style.display = l ? 'inline-block' : 'none';
  document.getElementById('form-error').textContent = '';
  updateCategoryList();
  document.getElementById('overlay').classList.add('open');
}

function closeModal(){
  document.getElementById('overlay').classList.remove('open');
  editingId = null;
}

async function saveCurrent(){
  const name = document.getElementById('f-name').value.trim();
  const url = document.getElementById('f-url').value.trim();
  const category = document.getElementById('f-category').value.trim() || 'Uncategorised';
  const status = document.getElementById('f-status').value;
  const errEl = document.getElementById('form-error');

  if(!name || !url){
    errEl.textContent = 'Name and URL are required.';
    return;
  }

  const body = JSON.stringify({name, url, category, status});
  const opts = {method: editingId ? 'PUT' : 'POST', headers: {'Content-Type': 'application/json'}, body};
  const endpoint = editingId ? `/api/links/${editingId}` : '/api/links';

  const res = await apiFetch(endpoint, opts);
  if(!res.ok){
    const data = await res.json().catch(() => ({}));
    errEl.textContent = data.error || 'Something went wrong.';
    return;
  }

  closeModal();
  await loadLinks();
}

async function deleteCurrent(){
  if(!editingId) return;
  const res = await apiFetch(`/api/links/${editingId}`, {method: 'DELETE'});
  if(!res.ok) return;
  closeModal();
  await loadLinks();
}

async function logout(){
  await fetch('/api/auth/logout', {method: 'POST'});
  window.location.href = '/';
}

function escapeHtml(s){
  const d = document.createElement('div');
  d.textContent = s == null ? '' : s;
  return d.innerHTML;
}

loadLinks();
