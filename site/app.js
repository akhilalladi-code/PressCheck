const $ = (id) => document.getElementById(id);
const API_BASE = String(window.PRESSCHECK_API_BASE || "").replace(/\/+$/, "");
let selectedFile = null;
let latestReport = null;

const profileDefaults = {
  "a4-flyer": [300, "3 mm bleed · 300 DPI · ±1 mm trim tolerance"],
  "a3-poster": [300, "3 mm bleed · 300 DPI · ±1 mm trim tolerance"],
  "business-card": [300, "3 mm bleed · 300 DPI · ±0.5 mm trim tolerance"],
  label: [300, "2 mm bleed · 300 DPI · ±0.5 mm trim tolerance"],
};

function setApiStatus(message, state = "offline") {
  const status = $("api-status");
  status.textContent = message;
  status.dataset.state = state;
}

async function checkApi() {
  if (!API_BASE) {
    setApiStatus("API URL NOT CONFIGURED");
    return;
  }
  setApiStatus("CONNECTING…", "checking");
  try {
    const response = await fetch(API_BASE + "/api/health", { cache: "no-store" });
    if (!response.ok) throw new Error("API returned " + response.status);
    const data = await response.json();
    if (data.status !== "ok" || data.engine !== "python") throw new Error("Unexpected API response");
    setApiStatus("PYTHON ENGINE ONLINE", "online");
  } catch {
    setApiStatus("API WAKING UP OR OFFLINE", "offline");
  }
}

function setFile(file) {
  if (!file) return;
  if (!/\.pdf$/i.test(file.name) || (file.type && file.type !== "application/pdf")) {
    showError("Choose a PDF file.");
    return;
  }
  if (file.size > 25 * 1024 * 1024) {
    showError("The hosted service currently accepts PDFs up to 25 MB.");
    return;
  }
  selectedFile = file;
  $("file-name").textContent = file.name;
  $("file-size").textContent = (file.size / 1024 / 1024).toFixed(2) + " MB";
  $("selected-file").hidden = false;
  $("dropzone").hidden = true;
  $("run").disabled = false;
  hideError();
}

function showError(message) {
  $("error").textContent = message;
  $("error").hidden = false;
}
function hideError() {
  $("error").hidden = true;
}

$("profile").addEventListener("change", () => {
  const [dpi, summary] = profileDefaults[$("profile").value];
  $("dpi").value = dpi;
  $("spec-summary").textContent = summary;
});
$("browse").addEventListener("click", () => $("file").click());
$("dropzone").addEventListener("click", (event) => {
  if (event.target.id !== "browse") $("file").click();
});
$("dropzone").addEventListener("keydown", (event) => {
  if (event.key === "Enter" || event.key === " ") {
    event.preventDefault();
    $("file").click();
  }
});
$("file").addEventListener("change", (event) => setFile(event.target.files[0]));
$("remove-file").addEventListener("click", () => {
  selectedFile = null;
  $("file").value = "";
  $("selected-file").hidden = true;
  $("dropzone").hidden = false;
  $("run").disabled = true;
});
for (const name of ["dragenter", "dragover"]) {
  $("dropzone").addEventListener(name, (event) => {
    event.preventDefault();
    $("dropzone").classList.add("dragover");
  });
}
for (const name of ["dragleave", "drop"]) {
  $("dropzone").addEventListener(name, (event) => {
    event.preventDefault();
    $("dropzone").classList.remove("dragover");
  });
}
$("dropzone").addEventListener("drop", (event) => setFile(event.dataTransfer.files[0]));

$("run").addEventListener("click", async () => {
  if (!selectedFile) return;
  if (!API_BASE) {
    showError("The hosted Python API has not been configured yet.");
    return;
  }
  const dpi = Number($("dpi").value);
  if (!Number.isInteger(dpi) || dpi < 72 || dpi > 1200) {
    showError("Minimum DPI must be a whole number between 72 and 1200.");
    return;
  }
  hideError();
  $("run").disabled = true;
  $("progress").hidden = false;
  $("progress").textContent = "Sending PDF securely to the Python preflight service…";
  try {
    const body = new FormData();
    body.append("file", selectedFile, selectedFile.name);
    body.append("profile", $("profile").value);
    body.append("min_dpi", String(dpi));
    const response = await fetch(API_BASE + "/api/preflight", {
      method: "POST",
      body,
      cache: "no-store",
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail || "Preflight failed with HTTP " + response.status + ".");
    latestReport = data;
    renderReport(data);
    $("results").hidden = false;
    $("results").scrollIntoView({ behavior: "smooth", block: "start" });
    setApiStatus("PYTHON ENGINE ONLINE", "online");
  } catch (error) {
    const message = error instanceof TypeError
      ? "Could not reach the Python API. It may be waking from its free-tier sleep; wait a minute and try again."
      : (error.message || "Could not inspect this PDF.");
    showError(message);
    setApiStatus("API UNAVAILABLE", "offline");
  } finally {
    $("progress").hidden = true;
    $("run").disabled = false;
  }
});

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[char]);
}

function renderReport(report) {
  const summary = report.summary;
  $("report-name").textContent = report.file_name;
  $("report-meta").textContent = report.profile.name + " · " + summary.pages +
    " pages · " + report.profile.bleed_mm + " mm bleed target · " +
    report.profile.min_dpi + " DPI threshold · Python engine";
  $("report-status").textContent = summary.status === "passed" ? "NO BLOCKING FINDINGS" : "NEEDS ATTENTION";
  $("report-status").className = "status" + (summary.status === "passed" ? "" : " attention");
  $("metrics").innerHTML = [
    ["PAGES", summary.pages], ["IMAGES", summary.images],
    ["ERRORS", summary.errors], ["WARNINGS", summary.warnings],
  ].map(([label, value]) =>
    '<div class="metric"><strong>' + value + '</strong><span>' + label + "</span></div>"
  ).join("");
  $("finding-count").textContent = report.findings.length + " CHECKS";
  $("findings").innerHTML = report.findings.map((finding) =>
    '<article class="finding"><div class="finding-top"><span class="severity ' +
    finding.severity + '">' + finding.severity + "</span>" +
    (finding.page ? '<span class="muted">· PAGE ' + finding.page + "</span>" : "") +
    '</div><p>' + escapeHtml(finding.message) + '</p><small>↳ ' +
    escapeHtml(finding.recommendation) + "</small></article>"
  ).join("");
  $("page-count").textContent = report.pages.length + " PAGES";
  $("pages").innerHTML = report.pages.map((page) =>
    '<div class="page-row"><div><b>Page ' + page.page + '</b><small>' +
    page.width_mm + " × " + page.height_mm + " mm · " + page.images.length +
    " images · " + page.fonts.length + ' fonts</small></div><span class="page-tag">' +
    page.bleed_mm + " MM BLEED</span></div>"
  ).join("");
}

function download(name, type, content) {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = name;
  anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

$("export-json").addEventListener("click", () => {
  if (latestReport) download("presscheck-report.json", "application/json", JSON.stringify(latestReport, null, 2));
});
$("export-csv").addEventListener("click", () => {
  if (!latestReport) return;
  const rows = [
    ["severity", "code", "page", "message", "recommendation"],
    ...latestReport.findings.map((finding) => [
      finding.severity, finding.code, finding.page ?? "", finding.message, finding.recommendation,
    ]),
  ];
  const csv = rows.map((row) => row.map((value) =>
    '"' + String(value).replace(/"/g, '""') + '"'
  ).join(",")).join("\r\n");
  download("presscheck-findings.csv", "text/csv;charset=utf-8", csv);
});
$("export-html").addEventListener("click", () => {
  if (!latestReport) return;
  const report = latestReport;
  const content = '<!doctype html><html lang="en"><meta charset="utf-8"><title>PressCheck report</title>' +
    '<style>body{font:14px Arial;max-width:900px;margin:40px auto;padding:0 20px;color:#18211e}' +
    '.finding{padding:14px 0;border-bottom:1px solid #ddd}</style>' +
    '<h1>PressCheck · Python preflight report</h1><p>' + escapeHtml(report.file_name) +
    " · " + escapeHtml(report.profile.name) + " · " + report.summary.pages + " pages</p><h2>" +
    report.summary.status.toUpperCase() + "</h2><h2>Findings</h2>" +
    report.findings.map((finding) => '<article class="finding"><b>' + escapeHtml(finding.severity) +
      "</b><p>" + escapeHtml(finding.message) + "</p><small>" +
      escapeHtml(finding.recommendation) + "</small></article>").join("") +
    "<h2>Page inspection</h2>" + report.pages.map((page) =>
      "<p>Page " + page.page + ": " + page.width_mm + " × " + page.height_mm +
      " mm · " + page.bleed_mm + " mm bleed · " + page.images.length + " images · " +
      page.fonts.length + " fonts</p>"
    ).join("") + "<hr><small>Advisory only; not PDF/X certification.</small></html>";
  download("presscheck-report.html", "text/html;charset=utf-8", content);
});

checkApi();
