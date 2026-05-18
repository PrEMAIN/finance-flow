import { api } from "./api.js";

let currentUser = null;
let categories = [];
let expenseChart = null;
let confirmCallback = null;

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

function showToast(message, type = "info") {
  const container = $("#toast-container");
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = message;
  container.appendChild(el);
  setTimeout(() => el.remove(), 4000);
}

function formatMoney(value) {
  return new Intl.NumberFormat("ru-RU", {
    style: "currency",
    currency: "RUB",
    maximumFractionDigits: 2,
  }).format(value);
}

function formatDate(iso) {
  return new Date(iso).toLocaleString("ru-RU", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function setDefaultTxDate() {
  const now = new Date();
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
  $("#tx-date").value = now.toISOString().slice(0, 16);
}

function showAuth() {
  $("#auth-screen").classList.remove("hidden");
  $("#app-screen").classList.add("hidden");
}

function showApp() {
  $("#auth-screen").classList.add("hidden");
  $("#app-screen").classList.remove("hidden");
}

async function initApp() {
  try {
    currentUser = await api.me();
    $("#user-name").textContent = currentUser.name;
    showApp();
    await loadCategories();
    await refreshAll();
    api.flushOfflineQueue();
    startNotificationPolling();
  } catch {
    api.setToken(null);
    showAuth();
  }
}

async function loadCategories() {
  categories = await api.getCategories();
  const selects = ["#tx-category", "#filter-category", "#limit-category"];
  selects.forEach((sel) => {
    const el = $(sel);
    if (!el) return;
    const isFilter = sel === "#filter-category";
    el.innerHTML = isFilter ? '<option value="">Все</option>' : "";
    categories.forEach((c) => {
      const opt = document.createElement("option");
      opt.value = c.id;
      opt.textContent = `${c.icon} ${c.name}`;
      el.appendChild(opt);
    });
  });
}

async function refreshAll() {
  await Promise.all([
    loadSummary(),
    loadChart(),
    loadRecentTransactions(),
    loadAllTransactions(),
    loadLimits(),
    loadGoals(),
    loadAchievements(),
    loadCategoriesList(),
    updateNotificationsBadge(),
  ]);
}

async function loadSummary() {
  const period = $("#chart-period")?.value || "month";
  const data = await api.getSummary(period);
  $("#summary-cards").innerHTML = `
    <div class="stat-card income"><span>Доходы</span><strong>${formatMoney(data.income)}</strong></div>
    <div class="stat-card expense"><span>Расходы</span><strong>${formatMoney(data.expense)}</strong></div>
    <div class="stat-card balance"><span>Баланс</span><strong>${formatMoney(data.balance)}</strong></div>
  `;
}

async function loadChart() {
  const period = $("#chart-period").value;
  const data = await api.getChart(period);
  const ctx = $("#expense-chart");
  if (expenseChart) expenseChart.destroy();

  if (!data.segments.length) {
    expenseChart = new Chart(ctx, {
      type: "doughnut",
      data: { labels: ["Нет данных"], datasets: [{ data: [1], backgroundColor: ["#e2e8f0"] }] },
      options: { plugins: { legend: { display: false } } },
    });
    return;
  }

  expenseChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: data.segments.map((s) => `${s.icon} ${s.name}`),
      datasets: [
        {
          data: data.segments.map((s) => s.amount),
          backgroundColor: data.segments.map((s) => s.color),
        },
      ],
    },
    options: {
      plugins: {
        legend: { position: "bottom" },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.label}: ${formatMoney(ctx.raw)}`,
          },
        },
      },
    },
  });
}

function renderTransactionItem(tx, showActions = true) {
  const sign = tx.type === "income" ? "+" : "−";
  return `
    <div class="transaction-item" data-id="${tx.id}">
      <div class="meta">
        <div class="icon" style="background:${tx.category?.color || "#eef4f8"}22">${tx.category?.icon || "📁"}</div>
        <div>
          <strong>${tx.category?.name || "—"}</strong>
          <div style="font-size:0.8rem;color:#666">${formatDate(tx.date)}${tx.comment ? ` · ${tx.comment}` : ""}</div>
        </div>
      </div>
      <div style="display:flex;align-items:center;gap:0.5rem">
        <span class="amount ${tx.type}">${sign}${formatMoney(tx.amount)}</span>
        ${showActions ? `<button class="btn btn-secondary" data-delete-tx="${tx.id}" style="padding:0.35rem 0.6rem">✕</button>` : ""}
      </div>
    </div>
  `;
}

async function loadRecentTransactions() {
  const items = await api.getTransactions({});
  const container = $("#recent-transactions");
  const recent = items.slice(0, 8);
  container.innerHTML = recent.length
    ? recent.map((tx) => renderTransactionItem(tx, false)).join("")
    : '<p class="empty-state">Пока нет операций</p>';
}

async function loadAllTransactions() {
  const params = {};
  const type = $("#filter-type")?.value;
  const categoryId = $("#filter-category")?.value;
  const dateFrom = $("#filter-from")?.value;
  const dateTo = $("#filter-to")?.value;
  const amountMin = $("#filter-min")?.value;
  const amountMax = $("#filter-max")?.value;

  if (type) params.type = type;
  if (categoryId) params.categoryId = categoryId;
  if (dateFrom) params.dateFrom = dateFrom;
  if (dateTo) params.dateTo = dateTo + "T23:59:59";
  if (amountMin) params.amountMin = amountMin;
  if (amountMax) params.amountMax = amountMax;

  const items = await api.getTransactions(params);
  const container = $("#all-transactions");
  container.innerHTML = items.length
    ? items.map((tx) => renderTransactionItem(tx)).join("")
    : '<p class="empty-state">Транзакции не найдены</p>';

  container.querySelectorAll("[data-delete-tx]").forEach((btn) => {
    btn.addEventListener("click", () => confirmDeleteTransaction(btn.dataset.deleteTx));
  });
}

async function loadLimits() {
  const limits = await api.getLimits();
  const container = $("#limits-list");
  container.innerHTML = limits.length
    ? limits
        .map(
          (l) => `
        <div class="limit-item">
          <div class="limit-header">
            <span>${l.category?.icon || ""} ${l.category?.name || "Категория"}</span>
            <span>${formatMoney(l.spent)} / ${formatMoney(l.amount)}</span>
          </div>
          <div class="progress-bar ${l.status}">
            <span style="width:${Math.min(l.progress * 100, 100)}%"></span>
          </div>
          <div style="margin-top:0.5rem;display:flex;justify-content:space-between;font-size:0.85rem">
            <span>${(l.progress * 100).toFixed(0)}% использовано</span>
            <button class="btn btn-secondary" data-delete-limit="${l.id}" style="padding:0.25rem 0.5rem">Удалить</button>
          </div>
        </div>`
        )
        .join("")
    : '<p class="empty-state">Лимиты не установлены</p>';

  container.querySelectorAll("[data-delete-limit]").forEach((btn) => {
    btn.addEventListener("click", () =>
      showConfirm("Удалить лимит по этой категории?", async () => {
        await api.deleteLimit(btn.dataset.deleteLimit);
        showToast("Лимит удалён");
        await loadLimits();
      })
    );
  });
}

async function loadGoals() {
  const goals = await api.getGoals();
  const container = $("#goals-list");
  container.innerHTML = goals.length
    ? goals
        .map(
          (g) => `
        <div class="goal-item">
          <div style="display:flex;justify-content:space-between;align-items:center">
            <strong>${g.description}</strong>
            <button class="btn btn-secondary" data-delete-goal="${g.id}" style="padding:0.25rem 0.5rem">✕</button>
          </div>
          <p>${formatMoney(g.currentAmount)} / ${formatMoney(g.targetAmount)} (${g.progressPercent}%)</p>
          <div class="progress-bar"><span style="width:${g.progressPercent}%"></span></div>
          <form class="filters" style="margin-top:0.75rem" data-contribute="${g.id}">
            <label>Внести<input type="number" name="amount" min="1" step="0.01" required placeholder="1000" /></label>
            <button type="submit" class="btn btn-primary">Пополнить</button>
          </form>
        </div>`
        )
        .join("")
    : '<p class="empty-state">Цели не созданы</p>';

  container.querySelectorAll("form[data-contribute]").forEach((form) => {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const amount = form.amount.value;
      await api.contributeGoal(form.dataset.contribute, amount);
      showToast("Сумма добавлена к цели", "achievement");
      await loadGoals();
      await loadAchievements();
    });
  });

  container.querySelectorAll("[data-delete-goal]").forEach((btn) => {
    btn.addEventListener("click", () =>
      showConfirm("Удалить эту цель?", async () => {
        await api.deleteGoal(btn.dataset.deleteGoal);
        showToast("Цель удалена");
        await loadGoals();
      })
    );
  });
}

async function loadAchievements() {
  const items = await api.getAchievements();
  $("#achievements-grid").innerHTML = items
    .map(
      (a) => `
    <div class="achievement-card ${a.unlocked ? "unlocked" : ""}">
      <div class="icon">${a.icon}</div>
      <strong>${a.name}</strong>
      <p style="font-size:0.85rem;color:#666">${a.description}</p>
    </div>`
    )
    .join("");
}

async function loadCategoriesList() {
  const container = $("#categories-list");
  const custom = categories.filter((c) => c.isCustom);
  container.innerHTML = `
    <p><strong>Системные:</strong> ${categories.filter((c) => !c.isCustom).map((c) => `${c.icon} ${c.name}`).join(", ")}</p>
    ${
      custom.length
        ? custom
            .map(
              (c) => `
          <div class="transaction-item">
            <span>${c.icon} ${c.name}</span>
            <button class="btn btn-secondary" data-delete-cat="${c.id}">Удалить</button>
          </div>`
            )
            .join("")
        : "<p class='empty-state'>Нет пользовательских категорий</p>"
    }`;

  container.querySelectorAll("[data-delete-cat]").forEach((btn) => {
    btn.addEventListener("click", () =>
      showConfirm("Удалить категорию?", async () => {
        await api.deleteCategory(btn.dataset.deleteCat);
        showToast("Категория удалена");
        await loadCategories();
        await refreshAll();
      })
    );
  });
}

async function updateNotificationsBadge() {
  const data = await api.getNotifications();
  const badge = $("#notif-badge");
  if (data.unreadCount > 0) {
    badge.textContent = data.unreadCount;
    badge.classList.remove("hidden");
  } else {
    badge.classList.add("hidden");
  }
}

function startNotificationPolling() {
  setInterval(updateNotificationsBadge, 15000);
}

function openTxModal(type) {
  $("#tx-type").value = type;
  $("#tx-modal-title").textContent = type === "income" ? "Добавить доход" : "Добавить расход";
  $("#tx-error").textContent = "";
  $("#tx-form").reset();
  setDefaultTxDate();
  $("#tx-modal").classList.remove("hidden");
}

function closeTxModal() {
  $("#tx-modal").classList.add("hidden");
}

function showConfirm(text, callback) {
  $("#confirm-text").textContent = text;
  confirmCallback = callback;
  $("#confirm-modal").classList.remove("hidden");
}

function closeConfirm() {
  $("#confirm-modal").classList.add("hidden");
  confirmCallback = null;
}

function confirmDeleteTransaction(id) {
  showConfirm("Удалить эту транзакцию? Баланс и статистика будут пересчитаны.", async () => {
    await api.deleteTransaction(id);
    showToast("Транзакция удалена");
    await refreshAll();
  });
}

// Auth tabs
$$("[data-auth-tab]").forEach((tab) => {
  tab.addEventListener("click", () => {
    $$("[data-auth-tab]").forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");
    const isLogin = tab.dataset.authTab === "login";
    $("#login-form").classList.toggle("hidden", !isLogin);
    $("#register-form").classList.toggle("hidden", isLogin);
  });
});

$("#login-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  $("#login-error").textContent = "";
  try {
    const res = await api.login({
      email: fd.get("email"),
      password: fd.get("password"),
    });
    api.setToken(res.token);
    await initApp();
  } catch (err) {
    $("#login-error").textContent = err.message;
  }
});

$("#register-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  $("#register-error").textContent = "";
  try {
    const res = await api.register({
      name: fd.get("name"),
      email: fd.get("email"),
      password: fd.get("password"),
    });
    api.setToken(res.token);
    showToast("Регистрация успешна!", "achievement");
    await initApp();
  } catch (err) {
    $("#register-error").textContent = err.message;
  }
});

$("#logout-btn").addEventListener("click", () => {
  api.setToken(null);
  currentUser = null;
  showAuth();
});

$$(".nav-tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    $$(".nav-tab").forEach((t) => t.classList.remove("active"));
    $$(".panel").forEach((p) => p.classList.remove("active"));
    tab.classList.add("active");
    $(`#panel-${tab.dataset.panel}`).classList.add("active");
  });
});

$("#quick-expense").addEventListener("click", () => openTxModal("expense"));
$("#quick-income").addEventListener("click", () => openTxModal("income"));
$$("[data-open-tx]").forEach((btn) => {
  btn.addEventListener("click", () => openTxModal(btn.dataset.openTx));
});

$("#tx-cancel").addEventListener("click", closeTxModal);
$("#tx-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  $("#tx-error").textContent = "";
  try {
    await api.createTransaction({
      amount: fd.get("amount"),
      type: fd.get("type"),
      categoryId: fd.get("categoryId"),
      date: new Date(fd.get("date")).toISOString(),
      comment: fd.get("comment"),
    });
    showToast("Успешно сохранено", "achievement");
    closeTxModal();
    await refreshAll();
  } catch (err) {
    if (err.message === "OFFLINE_QUEUED") {
      showToast("Нет сети — транзакция сохранена локально и будет отправлена позже", "warning");
      closeTxModal();
    } else {
      $("#tx-error").textContent = err.message;
    }
  }
});

$("#chart-period").addEventListener("change", async () => {
  await loadSummary();
  await loadChart();
});

$("#apply-filters").addEventListener("click", loadAllTransactions);

$("#limit-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  await api.createLimit({
    categoryId: fd.get("categoryId"),
    amount: fd.get("amount"),
  });
  showToast("Лимит установлен");
  e.target.reset();
  await loadLimits();
  await loadAchievements();
});

$("#goal-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  await api.createGoal({
    description: fd.get("description"),
    targetAmount: fd.get("targetAmount"),
    deadline: fd.get("deadline") || null,
  });
  showToast("Цель создана");
  e.target.reset();
  await loadGoals();
  await loadAchievements();
});

$("#category-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  await api.createCategory({
    name: fd.get("name"),
    icon: fd.get("icon") || "📁",
    color: fd.get("color"),
  });
  showToast("Категория добавлена");
  e.target.reset();
  await loadCategories();
  await refreshAll();
});

$("#export-csv").addEventListener("click", async () => {
  const blob = await api.exportCsv();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "finance_flow_report.csv";
  a.click();
  URL.revokeObjectURL(url);
  showToast("Отчёт загружен");
});

$("#notifications-btn").addEventListener("click", async () => {
  const data = await api.getNotifications();
  const list = $("#notifications-list");
  list.innerHTML = data.items.length
    ? data.items
        .map(
          (n) => `
      <div class="transaction-item" style="margin-bottom:0.5rem;${n.isRead ? "opacity:0.6" : ""}">
        <div>
          <strong>${n.title}</strong>
          <p style="margin:0.25rem 0;font-size:0.9rem">${n.message}</p>
          <small style="color:#888">${formatDate(n.createdAt)}</small>
        </div>
      </div>`
        )
        .join("")
    : '<p class="empty-state">Нет уведомлений</p>';
  $("#notifications-modal").classList.remove("hidden");
  await api.markAllNotificationsRead();
  await updateNotificationsBadge();
});

$("#close-notifications").addEventListener("click", () => {
  $("#notifications-modal").classList.add("hidden");
});

$("#mark-all-read").addEventListener("click", async () => {
  await api.markAllNotificationsRead();
  await updateNotificationsBadge();
  $("#notifications-modal").classList.add("hidden");
});

$("#confirm-cancel").addEventListener("click", closeConfirm);
$("#confirm-ok").addEventListener("click", async () => {
  if (confirmCallback) await confirmCallback();
  closeConfirm();
});

if (api.getToken()) {
  initApp();
} else {
  showAuth();
}
