const el = id => document.getElementById(id);
async function api(path, options = {}) {
  const response = await fetch(path, {credentials: 'same-origin', ...options});
  const data = await response.json();
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Request denied');
  return data;
}
function reset() {
  el('console').hidden = true; el('login').hidden = false;
  el('status').textContent = ''; el('records').textContent = '';
}
async function refresh() {
  try {
    const data = await api('/status');
    el('status').textContent = JSON.stringify(data, null, 2);
    el('audit').hidden = data.actor.role !== 'manager';
    el('console').hidden = false; el('login').hidden = true;
    el('message').textContent = 'Signed in · read-only staging access';
  } catch (error) { reset(); el('message').textContent = error.message; }
}
el('login').onsubmit = async event => {
  event.preventDefault();
  const form = new FormData(event.target);
  try {
    await api('/session', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(Object.fromEntries(form))});
    event.target.reset(); await refresh();
  } catch (error) { event.target.elements.password.value = ''; el('message').textContent = error.message; }
};
el('refresh').onclick = refresh;
el('logout').onclick = async () => {
  try { await api('/logout', {method: 'POST'}); reset(); el('message').textContent = 'Signed out'; }
  catch (error) { el('message').textContent = error.message; }
};
el('audit').onclick = async () => {
  try { el('records').textContent = JSON.stringify(await api('/audit'), null, 2); }
  catch (error) { el('message').textContent = error.message; }
};
refresh();
