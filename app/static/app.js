const currency = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
});

const state = {
  expenses: [],
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
    cell.colSpan = 4;
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

  row.append(description, categoryCell, date, amount);
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

  categorySelect.replaceChildren();
  for (const category of response.data.categories) {
    const option = document.createElement("option");
    option.value = category.id;
    option.textContent = category.name;
    categorySelect.append(option);
  }
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
  clearStatus();
  refreshButton.disabled = true;
  try {
    await loadCategoriesAndExpenses();
    await loadSummary();
  } catch (error) {
    showStatus(error.message, "error");
  } finally {
    refreshButton.disabled = false;
  }
}

async function handleExpenseSubmit(event) {
  event.preventDefault();
  clearStatus();
  submitButton.disabled = true;

  const formData = new FormData(expenseForm);
  const payload = {
    amount: formData.get("amount"),
    description: formData.get("description"),
    spent_on: formData.get("spent_on"),
    category_id: Number(formData.get("category_id")),
  };

  try {
    const created = await fetchJson("/expenses", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    monthInput.value = created.spent_on.slice(0, 7);
    expenseForm.elements.description.value = "";
    expenseForm.elements.amount.value = "";
    await Promise.all([loadExpenses(), loadSummary()]);
    showStatus("Expense added and totals refreshed.", "success");
  } catch (error) {
    showStatus(error.message, "error");
  } finally {
    submitButton.disabled = false;
  }
}

expenseForm.addEventListener("submit", handleExpenseSubmit);

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
