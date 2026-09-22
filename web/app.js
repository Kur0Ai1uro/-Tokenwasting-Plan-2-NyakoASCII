const state = {
  mode: "image",
  font: "standard",
  fonts: [],
  art: "",
  ok: false,
  timer: 0,
};

const $ = (id) => document.getElementById(id);

function api() {
  return window.pywebview.api;
}

function markSwitch(id, isSecond) {
  const group = $(id);
  group.classList.toggle("is-second", isSecond);
  group.querySelectorAll("button").forEach((button, index) => {
    button.classList.toggle("is-on", isSecond ? index === 1 : index === 0);
  });
}

function setTheme(theme) {
  document.documentElement.dataset.theme = theme;
  localStorage.setItem("nyako-theme", theme);
  markSwitch("theme-switch", theme === "dark");
}

function setMode(mode) {
  state.mode = mode;
  markSwitch("mode-switch", mode === "text");
  document.querySelectorAll("[data-panel]").forEach((panel) => {
    panel.hidden = panel.dataset.panel !== mode;
  });
  if (!state.art) {
    const preview = $("preview");
    preview.textContent = emptyHint();
    preview.classList.add("is-empty");
    preview.classList.remove("is-error");
  }
  schedule();
}

function payload() {
  return {
    mode: state.mode,
    text: $("source").value,
    font: state.font,
    decoration: $("decoration").value,
    space: Number($("space").value),
    columns: Number($("columns").value),
    brightness: Number($("brightness").value),
    contrast: Number($("contrast").value),
    aspect: Number($("aspect").value),
    invert: $("invert").checked,
    preset: $("preset").value,
    charset: $("charset").value,
  };
}

function emptyHint() {
  return state.mode === "text" ? "写一句话，预览会跟着出现" : "选择一张图片，开始转成 ASCII";
}

function showResult(result) {
  const preview = $("preview");
  state.ok = Boolean(result.ok && result.art);
  state.art = state.ok ? result.art : "";
  const message = result.message || "";
  preview.textContent = state.art || message || emptyHint();
  preview.classList.toggle("is-error", Boolean(message) && !result.ok);
  preview.classList.toggle("is-empty", !state.art && !message);
  $("copy").disabled = !state.ok;
  $("save").disabled = !state.ok;
  if (state.ok) {
    $("status").textContent = `${result.columns} 列 × ${result.rows} 行`;
  } else if (!message) {
    $("status").textContent = "";
  }
}

function schedule() {
  window.clearTimeout(state.timer);
  state.timer = window.setTimeout(renderNow, 150);
}

async function renderNow() {
  if (!window.pywebview) return;
  const result = await api().render(payload());
  showResult(result);
}

function renderFonts() {
  const query = $("font-filter").value.trim().toLowerCase();
  const list = $("font-list");
  list.replaceChildren();
  state.fonts
    .filter((name) => name.toLowerCase().includes(query))
    .forEach((name) => {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = name;
      button.classList.toggle("is-on", name === state.font);
      button.addEventListener("click", () => {
        state.font = name;
        renderFonts();
        schedule();
      });
      list.appendChild(button);
    });
}

function bindSlider(id, format) {
  const input = $(id);
  const label = $(`${id}-value`);
  const update = () => {
    label.textContent = format(input.value);
    schedule();
  };
  input.addEventListener("input", update);
  label.textContent = format(input.value);
}

async function boot() {
  const saved = localStorage.getItem("nyako-theme");
  setTheme(saved === "dark" ? "dark" : "light");
  const options = await api().options();
  state.fonts = options.fonts;
  state.font = options.fonts.includes("standard") ? "standard" : options.fonts[0];
  const decoration = $("decoration");
  options.decorations.forEach((item) => {
    const option = document.createElement("option");
    option.value = item.id;
    option.textContent = item.label;
    decoration.appendChild(option);
  });
  const preset = $("preset");
  options.presets.forEach((name) => {
    const option = document.createElement("option");
    option.value = name;
    option.textContent = name;
    if (name === "中") option.selected = true;
    preset.appendChild(option);
  });
  renderFonts();
}

document.querySelectorAll("#theme-switch button").forEach((button) => {
  button.addEventListener("click", () => setTheme(button.dataset.theme));
});
document.querySelectorAll("#mode-switch button").forEach((button) => {
  button.addEventListener("click", () => setMode(button.dataset.mode));
});

$("source").addEventListener("input", schedule);
$("font-filter").addEventListener("input", renderFonts);
$("decoration").addEventListener("change", schedule);
$("preset").addEventListener("change", schedule);
$("charset").addEventListener("input", schedule);
$("invert").addEventListener("change", schedule);
bindSlider("space", (value) => String(Math.round(value)));
bindSlider("columns", (value) => String(Math.round(value)));
bindSlider("brightness", (value) => Number(value).toFixed(2));
bindSlider("contrast", (value) => Number(value).toFixed(2));
bindSlider("aspect", (value) => Number(value).toFixed(2));

$("open-image").addEventListener("click", async () => {
  const chosen = await api().choose_image();
  if (!chosen || chosen.cancelled) return;
  $("filename").textContent = chosen.ok ? chosen.name : "无法打开这张图片";
  if (!chosen.ok) {
    showResult({ ok: false, art: "", message: "无法打开这张图片。", columns: 0, rows: 0 });
    return;
  }
  renderNow();
});

$("copy").addEventListener("click", async () => {
  if (!state.art) return;
  await api().copy_text(state.art);
  $("status").textContent = "已复制到剪贴板";
});

$("save").addEventListener("click", async () => {
  if (!state.art) return;
  const saved = await api().save_text(state.art);
  if (saved && saved.ok) $("status").textContent = "已保存";
});

window.addEventListener("pywebviewready", boot);
