let currentDate = "";

function isNearBottom(el) {
  return el.scrollHeight - el.scrollTop - el.clientHeight < 50;
}

function escapeHtml(line) {
  return line.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function colorize(line) {
  const escaped = escapeHtml(line);
  if (escaped.includes("ERROR")) return `<span class="log-ERROR">${escaped}</span>`;
  if (escaped.includes("WARNING")) return `<span class="log-WARNING">${escaped}</span>`;
  if (escaped.includes("INFO")) return `<span class="log-INFO">${escaped}</span>`;
  return escaped;
}

async function loadDates() {
  const res = await fetch("/logs/api/dates/");
  const data = await res.json();
  const select = document.getElementById("date-select");
  select.innerHTML = "";
  (data.dates || []).forEach((d, i) => {
    const opt = document.createElement("option");
    opt.value = d;
    opt.textContent = d + (i === 0 ? " (latest)" : "");
    select.appendChild(opt);
  });
  if (data.dates && data.dates.length) {
    currentDate = data.dates[0];
    select.value = currentDate;
  }
}

async function loadLogs() {
  const url = currentDate ? `/logs/api/?date=${encodeURIComponent(currentDate)}` : "/logs/api/";
  const res = await fetch(url);
  const data = await res.json();
  const box = document.getElementById("log-box");
  const shouldScroll = isNearBottom(box);
  if (data.lines) {
    box.innerHTML = data.lines.map(colorize).join("");
    document.getElementById("log-count").textContent = `${data.count} of ${data.total || data.count} lines`;
  } else {
    box.textContent = data.error || "No log data.";
    document.getElementById("log-count").textContent = "";
  }
  if (shouldScroll) box.scrollTop = box.scrollHeight;
}

document.getElementById("date-select").addEventListener("change", (e) => {
  currentDate = e.target.value;
  loadLogs();
});

(async () => {
  await loadDates();
  await loadLogs();
  setInterval(loadLogs, 3000);
})();
