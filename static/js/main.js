function toggleJobType() {
  const checked = document.querySelector('input[name="job_type"]:checked');
  const type = checked ? checked.value : "folder";
  document.getElementById("folder-fields").style.display = type === "folder" ? "" : "none";
  document.getElementById("db-fields").style.display = type === "db" ? "" : "none";
}

document.addEventListener("DOMContentLoaded", toggleJobType);

function showDbDetails(btn) {
  const { id, name, db, host, user, password, socket, port } = btn.dataset;
  document.getElementById("db-details-form").action = `/backups/${id}/edit_db`;
  document.getElementById("db-details-title").textContent = `Database Connection Details: ${name}`;
  document.getElementById("db-details-db").value = db || "";
  document.getElementById("db-details-host").value = host || "";
  document.getElementById("db-details-user").value = user || "";
  document.getElementById("db-details-password").value = password || "";
  document.getElementById("db-details-socket").value = socket || "";
  document.getElementById("db-details-port").value = port || "";
  document.getElementById("db-details-modal").style.display = "flex";
}

function closeDbDetails() {
  document.getElementById("db-details-modal").style.display = "none";
}

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeDbDetails();
});
