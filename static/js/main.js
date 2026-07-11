function toggleJobType() {
  const checked = document.querySelector('input[name="job_type"]:checked');
  const type = checked ? checked.value : "folder";
  document.getElementById("folder-fields").style.display = type === "folder" ? "" : "none";
  document.getElementById("db-fields").style.display = type === "db" ? "" : "none";
}

document.addEventListener("DOMContentLoaded", toggleJobType);
