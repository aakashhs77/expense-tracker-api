// Run with: node --test tests/test_frontend.js
const { test } = require("node:test");
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const vm = require("node:vm");

function element() {
  return {
    children: [], style: {}, value: "", elements: { description: {}, amount: {} },
    append(...children) { this.children.push(...children); },
    replaceChildren() { this.children = []; },
    addEventListener() {},
  };
}

function frontend() {
  const elements = new Map();
  const requests = [];
  const context = vm.createContext({
    Intl, Date,
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
      else if (options?.method === "POST") body = { spent_on: "2026-03-05" };
      else if (url === "/expenses") body = [{ description: "<b>Lunch</b>", amount: "12.50", spent_on: "2026-03-05", category: { name: "Food" } }];
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
