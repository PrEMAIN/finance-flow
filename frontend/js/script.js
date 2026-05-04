const API = '/api';
let token = localStorage.getItem('token');
let chart = null;

document.addEventListener('DOMContentLoaded', () => {
    if(token) showApp();
    setupAuth();
});

function setupAuth() {
    document.getElementById('login-form').onsubmit = async e => {
        e.preventDefault();
        const res = await fetch(`${API}/login`, { method:'POST', body:JSON.stringify({email: document.getElementById('l-email').value, password: document.getElementById('l-pass').value}), headers:{'Content-Type':'application/json'} });
        if(res.ok) {
            const data = await res.json();
            token = data.token; localStorage.setItem('token', token); showApp();
        } else alert('Ошибка входа');
    };
    document.getElementById('reg-form').onsubmit = async e => {
        e.preventDefault();
        const res = await fetch(`${API}/register`, { method:'POST', body:JSON.stringify({name: document.getElementById('r-name').value, email: document.getElementById('r-email').value, password: document.getElementById('r-pass').value}), headers:{'Content-Type':'application/json'} });
        if(res.ok) { alert('Успешно! Войдите.'); document.getElementById('show-login').click(); }
        else alert('Ошибка регистрации');
    };
    document.getElementById('show-reg').onclick = e => { e.preventDefault(); toggleScreen('reg-screen'); };
    document.getElementById('show-login').onclick = e => { e.preventDefault(); toggleScreen('auth-screen'); };
    document.getElementById('logout').onclick = () => { localStorage.removeItem('token'); location.reload(); };
}

function showApp() {
    document.getElementById('app-screen').classList.remove('hidden');
    document.getElementById('auth-screen').classList.add('hidden');
    loadDashboard();
    loadCategories();
    document.getElementById('tx-form').onsubmit = addTransaction;
    document.getElementById('export-btn').onclick = () => window.open(`${API}/export/csv`, '_blank');
}

async function loadDashboard() {
    const res = await fetch(`${API}/stats/monthly`, { headers:{'Authorization':`Bearer ${token}`} });
    const data = await res.json();
    const ctx = document.getElementById('expense-chart').getContext('2d');
    if(chart) chart.destroy();
    chart = new Chart(ctx, { type:'pie', {labels:Object.keys(data), datasets:[{Object.values(data), backgroundColor:['#FF6B6B','#4ECDC4','#FFE66D','#1B86C4','#95E1D3']}]}, options:{responsive:true, maintainAspectRatio:false} });
    updateTxList();
}

async function loadCategories() {
    // В реальном проекте: GET /api/categories. Здесь статика для академической сдачи
    const sel = document.getElementById('tx-cat');
    sel.innerHTML = '<option value="uuid1">Еда</option><option value="uuid2">Транспорт</option><option value="uuid3">Жилье</option>';
}

async function addTransaction(e) {
    e.preventDefault();
    const data = { amount: +document.getElementById('tx-amount').value, type: document.getElementById('tx-type').value, category_id: 'uuid1', comment: document.getElementById('tx-comment').value };
    const res = await fetch(`${API}/transactions`, { method:'POST', body:JSON.stringify(data), headers:{'Content-Type':'application/json','Authorization':`Bearer ${token}`} });
    if(res.ok) { updateTxList(); e.target.reset(); alert('Сохранено!'); }
    else alert('Ошибка');
}

async function updateTxList() {
    const res = await fetch(`${API}/transactions`, { headers:{'Authorization':`Bearer ${token}`} });
    const txs = await res.json();
    const list = document.getElementById('transactions');
    list.innerHTML = '';
    let bal = 0;
    txs.forEach(t => {
        bal += t.type==='income' ? t.amount : -t.amount;
        list.innerHTML += `<li><span>${t.date} | ${t.category}</span> <span class="${t.type}">${t.type==='income'?'+':'-'}${t.amount} ₽</span></li>`;
    });
    document.getElementById('balance').textContent = `${bal.toFixed(2)} ₽`;
}

function toggleScreen(id) {
    document.querySelectorAll('.screen').forEach(s => s.classList.add('hidden'));
    document.getElementById(id).classList.remove('hidden');
}