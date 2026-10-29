// Run with: node --test tests/test_frontend.js
const { test } = require("node:test");
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const vm = require("node:vm");

function element() {
  return {
    children: [], style: {}, value: "", elements: { description: { focus() {} }, amount: {} },
    append(...children) { this.children.push(...children); },
    replaceChildren() { this.children = []; },
    addEventListener() {},
    setAttribute() {},
    scrollIntoView() {},
  };
}

function frontend() {
  const elements = new Map();
  const requests = [];
  const context = vm.createContext({
    Intl, Date,
    window: { confirm: () => true },
    document: {
      querySelector(selector) {
        if (!elements.has(selector)) elements.set(selector, element());
        return elements.get(selector);
      },
      createElement: element,
    },
    FormData: class { get(key) { return { amount: "12.50", description: "Lunch", spent_on: "2026-03-05", category_id: "1" }[key]; } },
    fetch: async (url, options) => {
      requests.push({ url, options });
      let body;
      if (url === "/graphql") body = { data: { categories: [{ id: 1, name: "Food" }] } };
      else if (["POST", "PUT"].includes(options?.method)) body = { spent_on: "2026-03-05" };
      else if (url === "/expenses") body = [{ id: 1, category_id: 1, description: "<b>Lunch</b>", amount: "12.50", spent_on: "2026-03-05", category: { name: "Food" } }];
      else body = { total_spend: "12.50", categories: [{ category_name: "Food", total: "12.50", share_percentage: "100.00" }] };
      return { ok: true, json: async () => body };
    },
  });
  const source = readFileSync("app/static/app.js", "utf8");
  // Invoke initialization explicitly so each test can await completion.
  vm.runInContext(source.replace(/initialize\(\);\s*$/, ""), context);
  return { context, elements, requests };
}

test("initialization renders data, dates, and summary while preserving text", async () => {
  const { context, elements, requests } = frontend();
  await vm.runInContext("initialize()", context);
  assert.equal(elements.get("#summary-month").value, "2026-03");
  assert.equal(elements.get("#spent-on").value, "2026-03-01");
  assert.equal(elements.get("#expense-rows").children[0].children[0].textContent, "<b>Lunch</b>");
  assert.equal(elements.get("#summary-breakdown").children.length, 1);
  assert.equal(elements.get("#category-id").children[0].textContent, "Food");
  assert.equal(requests.length, 3);
});

test("submission refreshes expenses and summary and restores the button", async () => {
  const { context, elements, requests } = frontend();
  await vm.runInContext("handleExpenseSubmit({ preventDefault() {} })", context);
  assert.equal(requests[0].url, "/expenses");
  assert.equal(JSON.parse(requests[0].options.body).category_id, 1);
  assert.equal(elements.get("#summary-month").value, "2026-03");
  assert.equal(elements.get("#submit-button").disabled, false);
  assert.equal(elements.get("#status-message").className, "status visible success");
  assert.equal(requests.length, 3);
});

test("empty lists and failed refresh have readable states", async () => {
  const { context, elements } = frontend();
  vm.runInContext('renderExpenses(); renderSummary({ total_spend: "0", categories: [] })', context);
  assert.match(elements.get("#expense-rows").children[0].children[0].textContent, /No expenses/);
  assert.match(elements.get("#summary-breakdown").children[0].textContent, /No expenses/);
  vm.runInContext('fetch = async () => { throw new Error("Offline"); }', context);
  await vm.runInContext("refreshAll()", context);
  assert.equal(elements.get("#status-message").textContent, "Offline");
  assert.equal(elements.get("#refresh-button").disabled, false);
});

test("editing preloads the form and automatically refreshes table and summary", async () => {
  const { context, elements, requests } = frontend();
  await vm.runInContext("initialize()", context);
  vm.runInContext("startEditing(state.expenses[0])", context);
  assert.equal(elements.get("#expense-form").elements.description.value, "<b>Lunch</b>");
  assert.equal(elements.get("#category-id").value, "1");
  assert.equal(elements.get("#add-title").textContent, "Edit expense");
  requests.length = 0;
  await vm.runInContext("handleExpenseSubmit({ preventDefault() {} })", context);
  assert.equal(requests.length, 3);
  assert.equal(requests[1].url, "/expenses");
  assert.equal(requests[2].url, "/summary?month=2026-03");
  assert.equal(requests[0].url, "/expenses/1");
  assert.equal(requests[0].options.method, "PUT");
  assert.match(elements.get("#status-message").textContent, /Expense updated and totals refreshed/);
  assert.equal(elements.get("#add-title").textContent, "Add expense");
  assert.equal(elements.get("#expense-rows").children[0].children[4].children[0].disabled, false);
});

test("delete requires confirmation and refreshes table and summary after an empty 204 response", async () => {
  const { context, elements, requests } = frontend();
  await vm.runInContext("initialize()", context);
  requests.length = 0;
  vm.runInContext("window.confirm = () => false", context);
  await vm.runInContext("deleteExpense(state.expenses[0])", context);
  assert.equal(requests.length, 0);
  vm.runInContext(`
    window.confirm = () => true;
    fetch = async (url, options) => {
      if (url === '/expenses/1' && options?.method === 'DELETE') {
        return { ok: true, json: async () => { throw new SyntaxError('Empty response'); } };
      }
      if (url === '/expenses') return { ok: true, json: async () => [] };
      if (url.startsWith('/summary?')) return { ok: true, json: async () => ({ total_spend: '0', categories: [] }) };
      throw new Error('Unexpected request');
    };
  `, context);
  await vm.runInContext("deleteExpense(state.expenses[0])", context);
  assert.match(elements.get("#status-message").textContent, /Expense deleted and totals refreshed/);
  assert.equal(elements.get("#expense-rows").children.length, 1);
  assert.match(elements.get("#expense-rows").children[0].children[0].textContent, /No expenses/);
  assert.match(elements.get("#summary-breakdown").children[0].textContent, /No expenses/);
});

test("failed edit preserves input and failed delete remains retryable", async () => {
  const { context, elements } = frontend();
  await vm.runInContext("initialize()", context);
  vm.runInContext(`
    startEditing(state.expenses[0]);
    fetch = async () => ({ ok: false, json: async () => ({ detail: 'Save failed' }) });
  `, context);
  await vm.runInContext("handleExpenseSubmit({ preventDefault() {} })", context);
  assert.equal(elements.get("#add-title").textContent, "Edit expense");
  assert.equal(elements.get("#expense-form").elements.description.value, "<b>Lunch</b>");
  assert.equal(elements.get("#submit-button").disabled, false);
  await vm.runInContext("deleteExpense(state.expenses[0])", context);
  assert.equal(elements.get("#status-message").textContent, "Save failed");
  assert.equal(elements.get("#expense-rows").children[0].children[4].children[1].disabled, false);
  vm.runInContext("stopEditing()", context);
  assert.equal(elements.get("#cancel-edit-button").hidden, true);
});
