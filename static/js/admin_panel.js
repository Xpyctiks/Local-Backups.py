function editRemoteServer(btn) {
  const form = document.getElementById("remote-form");
  if (!form) return;
  const { id, name, address, port } = btn.dataset;
  form.action = `/admin_panel/remotes/${id}/edit`;
  document.getElementById("remote-name").value = name;
  document.getElementById("remote-address").value = address;
  document.getElementById("remote-port").value = port;
  document.getElementById("remote-form-title").textContent = `Edit Remote Server: ${name}`;
  document.getElementById("remote-form-submit").textContent = "Save Changes";
  document.getElementById("remote-form-cancel").style.display = "";
  form.scrollIntoView({ behavior: "smooth", block: "center" });
}

function resetRemoteServerForm() {
  const form = document.getElementById("remote-form");
  if (!form) return;
  form.action = "/admin_panel/remotes/add";
  form.reset();
  document.getElementById("remote-form-title").textContent = "Add New Remote Server";
  document.getElementById("remote-form-submit").textContent = "Add Remote Server";
  document.getElementById("remote-form-cancel").style.display = "none";
}

document.querySelectorAll(".delete-remote-form").forEach((form) => {
  form.addEventListener("submit", (e) => {
    if (!confirm(`Delete remote server ${form.dataset.name}?`)) {
      e.preventDefault();
    }
  });
});
