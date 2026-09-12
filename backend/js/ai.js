// BilimSari AI tutor client
(function () {
  async function askAI(message, context) {
    const lang = (window.BS_I18N && BS_I18N.getLang()) || 'uz';
    const res = await fetch('/api/ai/tutor', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: message,
        context: context || '',
        lang: lang,
      }),
    });
    const data = await res.json().catch(function () { return {}; });
    return data;
  }

  function ensurePanel() {
    if (document.getElementById('aiPanel')) return;
    const style = document.createElement('style');
    style.textContent = `
      #aiFab {
        position: fixed; right: 16px; bottom: 88px; z-index: 60;
        width: 56px; height: 56px; border-radius: 50%;
        background: #58A700; color: #fff; border: none;
        font-weight: 800; font-size: 14px; cursor: pointer;
        box-shadow: 0 6px 20px rgba(88,167,0,.35);
      }
      #aiPanel {
        display: none; position: fixed; inset: 0; z-index: 90;
        background: rgba(0,0,0,.4); align-items: flex-end; justify-content: center;
      }
      #aiPanel.open { display: flex; }
      #aiSheet {
        background: #fff; width: 100%; max-width: 480px;
        max-height: 80vh; border-radius: 20px 20px 0 0;
        display: flex; flex-direction: column;
        padding-bottom: env(safe-area-inset-bottom);
      }
      #aiHead {
        display: flex; align-items: center; justify-content: space-between;
        padding: 14px 16px; border-bottom: 1px solid #eee; font-weight: 800;
      }
      #aiClose {
        border: none; background: #f2f2f2; width: 36px; height: 36px;
        border-radius: 50%; font-size: 18px; cursor: pointer;
      }
      #aiMessages {
        flex: 1; overflow-y: auto; padding: 14px 16px;
        display: flex; flex-direction: column; gap: 10px; min-height: 200px;
      }
      .ai-msg {
        max-width: 90%; padding: 10px 14px; border-radius: 14px;
        font-size: 14px; line-height: 1.45; white-space: pre-wrap;
      }
      .ai-msg.bot { background: #f0f7e8; align-self: flex-start; }
      .ai-msg.user { background: #e8f1ff; align-self: flex-end; }
      .ai-msg.err { background: #ffecec; color: #b00; }
      #aiForm {
        display: flex; gap: 8px; padding: 12px 14px;
        border-top: 1px solid #eee;
      }
      #aiInput {
        flex: 1; height: 44px; border: 2px solid #e5e5e5;
        border-radius: 12px; padding: 0 12px; font-size: 15px; outline: none;
      }
      #aiInput:focus { border-color: #58A700; }
      #aiSend {
        height: 44px; padding: 0 16px; border: none; border-radius: 12px;
        background: #58A700; color: #fff; font-weight: 800; cursor: pointer;
      }
      #aiSend:disabled { opacity: .6; }
    `;
    document.head.appendChild(style);

    const fab = document.createElement('button');
    fab.id = 'aiFab';
    fab.type = 'button';
    fab.textContent = 'AI';
    fab.title = 'AI yordamchi';
    fab.onclick = openAI;
    document.body.appendChild(fab);

    const panel = document.createElement('div');
    panel.id = 'aiPanel';
    panel.onclick = function (e) { if (e.target === panel) closeAI(); };
    panel.innerHTML = `
      <div id="aiSheet">
        <div id="aiHead">
          <span>AI yordamchi</span>
          <button type="button" id="aiClose" aria-label="Yopish">×</button>
        </div>
        <div id="aiMessages"></div>
        <form id="aiForm">
          <input id="aiInput" type="text" placeholder="Savolingizni yozing..." autocomplete="off">
          <button type="submit" id="aiSend">Yuborish</button>
        </form>
      </div>
    `;
    document.body.appendChild(panel);
    document.getElementById('aiClose').onclick = closeAI;
    document.getElementById('aiForm').onsubmit = function (e) {
      e.preventDefault();
      sendFromInput();
    };
  }

  function openAI() {
    ensurePanel();
    document.getElementById('aiPanel').classList.add('open');
    const box = document.getElementById('aiMessages');
    if (box && !box.dataset.greeted) {
      box.dataset.greeted = '1';
      addMsg('bot', 'Salom! Men BilimSari AI yordamchisiman. Dars yoki fan bo‘yicha savolingizni yozing.');
    }
    setTimeout(function () {
      const inp = document.getElementById('aiInput');
      if (inp) inp.focus();
    }, 200);
  }

  function closeAI() {
    const p = document.getElementById('aiPanel');
    if (p) p.classList.remove('open');
  }

  function addMsg(role, text) {
    const box = document.getElementById('aiMessages');
    if (!box) return;
    const el = document.createElement('div');
    el.className = 'ai-msg ' + role;
    el.textContent = text;
    box.appendChild(el);
    box.scrollTop = box.scrollHeight;
  }

  async function sendFromInput() {
    const inp = document.getElementById('aiInput');
    const btn = document.getElementById('aiSend');
    const text = (inp && inp.value || '').trim();
    if (!text) return;
    inp.value = '';
    addMsg('user', text);
    if (btn) btn.disabled = true;
    addMsg('bot', '...');
    const box = document.getElementById('aiMessages');
    const pending = box && box.lastElementChild;
    try {
      const data = await askAI(text, window.__AI_CONTEXT || '');
      if (pending) pending.remove();
      if (data.ok && data.reply) {
        addMsg('bot', data.reply);
      } else {
        addMsg('err', (data && data.error) || 'AI javob bermadi');
      }
    } catch (e) {
      if (pending) pending.remove();
      addMsg('err', 'Tarmoq xatosi');
    }
    if (btn) btn.disabled = false;
  }

  /** Darsda noto‘g‘ri javobni tushuntirish */
  async function explainWrong(question, correct, userAnswer, subject) {
    const msg = 'Bu savolni tushuntirib ber. Nima uchun to‘g‘ri javob shu?';
    const ctx = [
      subject ? ('Fan: ' + subject) : '',
      'Savol: ' + (question || ''),
      'To‘g‘ri javob: ' + (correct || ''),
      userAnswer != null ? ('O‘quvchi javobi: ' + userAnswer) : '',
    ].filter(Boolean).join('\\n');
    return askAI(msg, ctx);
  }

  window.BilimSariAI = {
    askAI: askAI,
    openAI: openAI,
    closeAI: closeAI,
    explainWrong: explainWrong,
    ensurePanel: ensurePanel,
  };

  // Auto FAB on pages that include this script
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', ensurePanel);
  } else {
    ensurePanel();
  }
})();
