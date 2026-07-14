function toggleJobType() {
  const checked = document.querySelector('input[name="job_type"]:checked');
  const type = checked ? checked.value : "folder";
  document.getElementById("folder-fields").style.display = type === "folder" ? "" : "none";
  document.getElementById("db-fields").style.display = type === "db" ? "" : "none";
}

document.addEventListener("DOMContentLoaded", toggleJobType);

function showDbDetails(btn) {
  const { name, db, host, user, password, socket, port } = btn.dataset;
  document.getElementById("db-details-title").textContent = `Database Connection Details: ${name}`;
  document.getElementById("db-details-db").textContent = db || "-";
  document.getElementById("db-details-host").textContent = host || "(default)";
  document.getElementById("db-details-user").textContent = user || "(default)";
  document.getElementById("db-details-password").textContent = password || "(default)";
  document.getElementById("db-details-socket").textContent = socket || "(default)";
  document.getElementById("db-details-port").textContent = port || "(default)";
  document.getElementById("db-details-modal").style.display = "flex";
}

function closeDbDetails() {
  document.getElementById("db-details-modal").style.display = "none";
}

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeDbDetails();
});
