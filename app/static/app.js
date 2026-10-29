const currency = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
});

const state = {
  expenses: [],
  editingId: null,
  busy: false,
};

const expenseRows = document.querySelector("#expense-rows");
const expenseCount = document.querySelector("#expense-count");
const expenseForm = document.querySelector("#expense-form");
const categorySelect = document.querySelector("#category-id");
const spentOnInput = document.querySelector("#spent-on");
const monthInput = document.querySelector("#summary-month");
const totalSpend = document.querySelector("#total-spend");
const summaryBreakdown = document.querySelector("#summary-breakdown");
const statusMessage = document.querySelector("#status-message");
const submitButton = document.querySelector("#submit-button");
const refreshButton = document.querySelector("#refresh-button");

const formTitle = document.querySelector("#add-title");
const formDescription = document.querySelector("#form-description");
const cancelEditButton = document.querySelector("#cancel-edit-button");

function currentMonth() {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  return `${now.getFullYear()}-${month}`;
}

function showStatus(message, type) {
  statusMessage.textContent = message;
  statusMessage.className = `status visible ${type}`;
}

function clearStatus() {
  statusMessage.textContent = "";
  statusMessage.className = "status";
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  const body = await response.json().catch(() => null);

  if (!response.ok) {
    const detail = body?.detail;
    const message = typeof detail === "string"
      ? detail
      : "The API request failed.";
    throw new Error(message);
  }

  return body;
}

function renderExpenses() {
  expenseRows.replaceChildren();
  expenseCount.textContent = `${state.expenses.length} expense${
    state.expenses.length === 1 ? "" : "s"
  }`;

  if (state.expenses.length === 0) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 5;
    cell.className = "empty-cell";
    cell.textContent = "No expenses have been recorded yet.";
    row.append(cell);
    expenseRows.append(row);
    return;
  }

  for (const expense of [...state.expenses].reverse()) {
    expenseRows.append(createExpenseRow(expense));
  }
}

function formatExpenseDate(spentOn) {
  return new Date(`${spentOn}T00:00:00`).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function createExpenseRow(expense) {
  const row = document.createElement("tr");
  const description = document.createElement("td");
  const categoryCell = document.createElement("td");
  const category = document.createElement("span");
  const date = document.createElement("td");
  const amount = document.createElement("td");

  description.textContent = expense.description;
  category.className = "category-badge";
  category.textContent = expense.category.name;
  categoryCell.append(category);
  date.textContent = formatExpenseDate(expense.spent_on);
  amount.className = "amount-cell";
  amount.textContent = currency.format(Number(expense.amount));

  const actions = document.createElement("td");
  const editButton = document.createElement("button");
  const deleteButton = document.createElement("button");
  editButton.type = deleteButton.type = "button";
  editButton.className = "row-button";
  deleteButton.className = "row-button delete-button";
  editButton.textContent = "Edit";
  deleteButton.textContent = "Delete";
  editButton.setAttribute("aria-label", `Edit ${expense.description}`);
  deleteButton.setAttribute("aria-label", `Delete ${expense.description}`);
  editButton.disabled = deleteButton.disabled = state.busy;
  editButton.addEventListener("click", () => startEditing(expense));
  deleteButton.addEventListener("click", () => deleteExpense(expense));
  actions.append(editButton, deleteButton);
  row.append(description, categoryCell, date, amount, actions);
  return row;
}

async function loadExpenses() {
  state.expenses = await fetchJson("/expenses");
  renderExpenses();
}

async function loadCategories() {
  const response = await fetchJson("/graphql", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query: "query { categories { id name } }",
    }),
  });

  if (response.errors) {
    throw new Error(response.errors[0]?.message || "GraphQL request failed.");
  }

  const selectedCategory = categorySelect.value;
  categorySelect.replaceChildren();
  for (const category of response.data.categories) {
    const option = document.createElement("option");
    option.value = category.id;
    option.textContent = category.name;
    categorySelect.append(option);
  }
  if (selectedCategory) categorySelect.value = selectedCategory;
}

function renderSummary(summary) {
  totalSpend.textContent = currency.format(Number(summary.total_spend));
  summaryBreakdown.replaceChildren();

  if (summary.categories.length === 0) {
    const message = document.createElement("p");
    message.className = "empty-cell";
    message.textContent = "No expenses for this month.";
    summaryBreakdown.append(message);
    return;
  }

  for (const item of summary.categories) {
    summaryBreakdown.append(createSummaryRow(item));
  }
}

function createSummaryRow(item) {
  const row = document.createElement("div");
  const heading = document.createElement("div");
  const name = document.createElement("span");
  const value = document.createElement("span");
  const track = document.createElement("div");
  const fill = document.createElement("div");

  row.className = "breakdown-row";
  heading.className = "breakdown-heading";
  name.className = "breakdown-name";
  value.className = "breakdown-value";
  track.className = "bar-track";
  fill.className = "bar-fill";

  name.textContent = item.category_name;
  value.textContent = `${currency.format(Number(item.total))} · ${
    item.share_percentage
  }%`;
  fill.style.width = `${Math.min(Number(item.share_percentage), 100)}%`;

  heading.append(name, value);
  track.append(fill);
  row.append(heading, track);
  return row;
}

async function loadSummary() {
  if (!monthInput.value) {
    return;
  }

  const summary = await fetchJson(
    `/summary?month=${encodeURIComponent(monthInput.value)}`
  );
  renderSummary(summary);
}

async function loadCategoriesAndExpenses() {
  await Promise.all([loadCategories(), loadExpenses()]);
}

async function refreshAll() {
  if (state.busy) return;
  clearStatus();
  setBusy(true);
  try {
    await loadCategoriesAndExpenses();
    await loadSummary();
  } catch (error) {
    showStatus(error.message, "error");
  } finally {
    setBusy(false);
  }
}

function setBusy(busy) {
  state.busy = busy;
  submitButton.disabled = cancelEditButton.disabled = refreshButton.disabled = busy;
  renderExpenses();
}

function startEditing(expense) {
  if (state.busy) return;
  clearStatus();
  state.editingId = expense.id;
  expenseForm.elements.description.value = expense.description;
  expenseForm.elements.amount.value = expense.amount;
  spentOnInput.value = expense.spent_on;
  categorySelect.value = String(expense.category_id);
  formTitle.textContent = "Edit expense";
  formDescription.textContent = "Update this transaction and its monthly summary.";
  submitButton.textContent = "Save changes";
  cancelEditButton.hidden = false;
  expenseForm.scrollIntoView({ behavior: "smooth", block: "center" });
  expenseForm.elements.description.focus();
}

function stopEditing() {
  state.editingId = null;
  expenseForm.elements.description.value = "";
  expenseForm.elements.amount.value = "";
  formTitle.textContent = "Add expense";
  formDescription.textContent = "Record a new transaction";
  submitButton.textContent = "Add expense";
  cancelEditButton.hidden = true;
}

async function refreshExpenseViews(action) {
  try {
    await Promise.all([loadExpenses(), loadSummary()]);
    showStatus(`Expense ${action} and totals refreshed.`, "success");
  } catch (error) {
    showStatus(`Expense ${action}, but refreshing failed: ${error.message} Click Refresh data to retry.`, "error");
  }
}

async function deleteExpense(expense) {
  if (state.busy) return;
  if (!window.confirm(`Delete "${expense.description}"? This cannot be undone.`)) return;
  clearStatus();
  setBusy(true);
  try {
    await fetchJson(`/expenses/${expense.id}`, { method: "DELETE" });
    if (state.editingId === expense.id) stopEditing();
    await refreshExpenseViews("deleted");
  } catch (error) {
    showStatus(error.message, "error");
  } finally {
    setBusy(false);
  }
}

async function handleExpenseSubmit(event) {
  event.preventDefault();
  if (state.busy) return;
  clearStatus();
  const editingId = state.editingId;

  const formData = new FormData(expenseForm);
  const payload = {
    amount: formData.get("amount"),
    description: formData.get("description"),
    spent_on: formData.get("spent_on"),
    category_id: Number(formData.get("category_id")),
  };

  setBusy(true);
  try {
    const saved = await fetchJson(editingId === null ? "/expenses" : `/expenses/${editingId}`, {
      method: editingId === null ? "POST" : "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    stopEditing();
    monthInput.value = saved.spent_on.slice(0, 7);
    await refreshExpenseViews(editingId === null ? "added" : "updated");
  } catch (error) {
    showStatus(error.message, "error");
  } finally {
    setBusy(false);
  }
}

expenseForm.addEventListener("submit", handleExpenseSubmit);
cancelEditButton.addEventListener("click", () => {
  if (!state.busy) stopEditing();
});

monthInput.addEventListener("change", () => {
  loadSummary().catch((error) => showStatus(error.message, "error"));
});

refreshButton.addEventListener("click", refreshAll);

async function initialize() {
  try {
    await loadCategoriesAndExpenses();
    const latestMonth = state.expenses.at(-1)?.spent_on.slice(0, 7)
      || currentMonth();
    monthInput.value = latestMonth;
    spentOnInput.value = `${latestMonth}-01`;
    await loadSummary();
  } catch (error) {
    showStatus(error.message, "error");
  }
}

initialize();
