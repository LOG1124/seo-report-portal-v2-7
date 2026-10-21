'use strict';
(() => {
  const token = location.hash.slice(1);
  const notice = document.querySelector('#notice');
  const notify = (message, error = false) => {
    notice.className = error ? 'error' : '';
    notice.replaceChildren();
    const text = document.createElement('p');
    text.textContent = message;
    notice.append(text);
  };
  const request = async (path, data) => {
    const options = {headers: {'X-Setup-Token': token}, cache: 'no-store'};
    if (data !== undefined) {
      options.method = 'POST';
      options.headers['Content-Type'] = 'application/json';
      options.body = JSON.stringify(data);
    }
    let response;
    try { response = await fetch(path, options); }
    catch { throw new Error('本机服务未响应，请检查是否已关闭或过期。'); }
    let result;
    try { result = await response.json(); }
    catch { throw new Error('本机服务返回了无法读取的结果。'); }
    if (!response.ok) throw new Error(result.error || '未完成保存，请检查配置。');
    return result;
  };
  const refresh = async () => {
    const result = await request('/api/status');
    document.querySelector('#workspace').textContent = result.workspace;
    document.querySelector('#environment-note').textContent = result.google_env_override ? '检测到 GOOGLE_APPLICATION_CREDENTIALS：它优先于 Google 配置中的凭据路径，请核对实际身份。' : '';
    document.querySelector('#mcp-path').textContent = '接入目标：' + result.codex_config + '。不勾选时只保存本机配置片段。';
    const integrate = document.querySelector('#integrate');
    integrate.disabled = !result.mcp_auto_merge;
    if (!result.mcp_auto_merge) document.querySelector('#mcp-path').textContent += ' 自动接入需要 Python 3.11+，本次可先保存片段。';
    const list = document.querySelector('#files');
    list.replaceChildren();
    for (const file of result.files) {
      const row = document.createElement('li');
      const state = document.createElement('span');
      state.className = 'file-status' + (file.exists ? ' exists' : '');
      state.textContent = file.exists ? '已有文件' : '尚未创建';
      const path = document.createElement('code');
      path.textContent = file.path;
      row.append(state, path);
      list.append(row);
    }
  };
  for (const button of document.querySelectorAll('.nav')) button.addEventListener('click', () => {
    notice.replaceChildren();
    notice.className = '';
    for (const panel of document.querySelectorAll('.panel')) panel.hidden = panel.id !== button.dataset.panel;
    for (const nav of document.querySelectorAll('.nav')) {
      const active = nav === button;
      nav.classList.toggle('active', active);
      if (active) nav.setAttribute('aria-current', 'step'); else nav.removeAttribute('aria-current');
    }
  });
  for (const form of document.querySelectorAll('form')) form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const submit = form.querySelector('button[type=submit]');
    const label = submit.textContent;
    submit.disabled = true;
    submit.textContent = '正在本机保存…';
    const data = {};
    try {
      for (const input of form.querySelectorAll('input')) {
        if (input.type === 'file') {
          if (input.files[0]) {
            if (input.files[0].size > 128 * 1024) throw new Error('Google JSON 超过 128 KB，请检查选中的文件。');
            data[input.name] = await input.files[0].text();
          }
        } else data[input.name] = input.type === 'checkbox' ? input.checked : input.value;
      }
      const result = await request('/api/save/' + form.dataset.group, data);
      notify(result.message);
      for (const [title, paths] of [['保存位置', result.files], ['备份位置', result.backups]]) {
        if (!paths.length) continue;
        const heading = document.createElement('strong');
        heading.textContent = title;
        const list = document.createElement('ul');
        for (const path of paths) { const item = document.createElement('li'); item.textContent = path; list.append(item); }
        notice.append(heading, list);
      }
      for (const input of form.querySelectorAll('input[type=password],input[type=file]')) input.value = '';
      for (const checkbox of form.querySelectorAll('input[type=checkbox]')) checkbox.checked = false;
      try { await refresh(); } catch { const detail = document.createElement('p'); detail.textContent = '文件已保存；刷新列表失败，可稍后重试。'; notice.append(detail); }
    } catch (error) { notify(error.message, true); }
    finally {
      // Submitted values never enter browser storage, console messages or URLs.
      for (const key of Object.keys(data)) delete data[key];
      submit.disabled = false;
      submit.textContent = label;
      notice.scrollIntoView({block: 'nearest', behavior: 'auto'});
    }
  });
  document.querySelector('#refresh').addEventListener('click', () => refresh().catch(error => notify(error.message, true)));
  document.querySelector('#stop').addEventListener('click', async () => {
    try {
      const result = await request('/api/stop', {});
      for (const form of document.querySelectorAll('form')) form.reset();
      for (const input of document.querySelectorAll('input,button')) input.disabled = true;
      notify(result.message);
    } catch (error) { notify(error.message, true); }
  });
  window.addEventListener('pagehide', () => { for (const form of document.querySelectorAll('form')) form.reset(); });
  if (!token) notify('请使用终端或 Codex 给出的完整本机链接打开页面。链接中的会话标识缺失。', true);
  else refresh().catch(error => notify(error.message, true));
})();
