// Relative URL "/api/..." — nginx adha backend-ku proxy pannum
const API = "/api";

const form = document.getElementById("task-form");
const titleInput = document.getElementById("task-title");
const list = document.getElementById("task-list");
const emptyState = document.getElementById("empty");
const errorBox = document.getElementById("error");

async function request(path, options = {}) {
  const response = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.error || `Request failed (${response.status})`);
  }
  return response.status === 204 ? null : response.json();
}

function showError(message) {
  errorBox.textContent = message;
  errorBox.hidden = !message;
}

function renderTasks(tasks) {
  list.replaceChildren(
    ...tasks.map((task) => {
      const item = document.createElement("li");
      item.classList.toggle("done", task.done);

      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.checked = task.done;
      checkbox.addEventListener("change", () => updateTask(task.id, { done: checkbox.checked }));

      const title = document.createElement("span");
      title.textContent = task.title;

      const remove = document.createElement("button");
      remove.textContent = "Delete";
      remove.addEventListener("click", () => deleteTask(task.id));

      item.append(checkbox, title, remove);
      return item;
    }),
  );
  emptyState.hidden = tasks.length > 0;
}

async function loadTasks() {
  try {
    renderTasks(await request("/tasks"));
    showError("");
  } catch (error) {
    showError(error.message);
  }
}

async function updateTask(id, changes) {
  try {
    await request(`/tasks/${id}`, { method: "PATCH", body: JSON.stringify(changes) });
  } catch (error) {
    showError(error.message);
  }
  loadTasks();
}

async function deleteTask(id) {
  try {
    await request(`/tasks/${id}`, { method: "DELETE" });
  } catch (error) {
    showError(error.message);
  }
  loadTasks();
}

// Ovvoru 3 sec-kum health call — K8s-la replicas > 1 irundha hostname maaradhu paakalaam
async function loadBackendInfo() {
  try {
    const info = await request("/health");
    document.getElementById("backend-name").textContent = info.backend;
    document.getElementById("backend-host").textContent = info.hostname;
  } catch (error) {
    document.getElementById("backend-name").textContent = "unreachable";
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const title = titleInput.value.trim();
  if (!title) return;
  try {
    await request("/tasks", { method: "POST", body: JSON.stringify({ title }) });
    titleInput.value = "";
  } catch (error) {
    showError(error.message);
  }
  loadTasks();
});

loadBackendInfo();
loadTasks();
setInterval(loadBackendInfo, 3000);
