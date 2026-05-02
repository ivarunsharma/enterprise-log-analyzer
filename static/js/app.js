var form = document.getElementById("upload-form");
var fileInput = document.getElementById("file-input");
var dropZone = document.getElementById("drop-zone");
var fileNameDiv = document.getElementById("file-name");
var fileNameText = document.getElementById("file-name-text");
var progressDiv = document.getElementById("progress");
var progressText = document.getElementById("progress-text");
var progressBar = document.getElementById("progress-bar");
var submitBtn = document.getElementById("submit-btn");

// Timers for the progress label updates during analysis
var progressTimers = [];

if (fileInput) {
  fileInput.addEventListener("change", function () {
    if (fileInput.files[0]) {
      showFileName(fileInput.files[0].name);
    }
  });
}

if (dropZone) {
  dropZone.addEventListener("dragover", function (e) {
    e.preventDefault();
    dropZone.classList.add("drag-over");
  });

  dropZone.addEventListener("dragleave", function () {
    dropZone.classList.remove("drag-over");
  });

  dropZone.addEventListener("drop", function (e) {
    e.preventDefault();
    dropZone.classList.remove("drag-over");
    var file = e.dataTransfer.files[0];
    if (file) {
      fileInput.files = e.dataTransfer.files;
      showFileName(file.name);
    }
  });
}

function showFileName(name) {
  fileNameText.textContent = name;
  fileNameDiv.classList.remove("hidden");
}

if (form) {
  form.addEventListener("submit", async function (e) {
    e.preventDefault();
    if (!fileInput.files[0]) return;

    submitBtn.disabled = true;
    progressDiv.classList.remove("hidden");
    form.classList.add("opacity-50", "pointer-events-none");

    // Collect which severity checkboxes are checked
    var checkboxes = form.querySelectorAll("input[type=checkbox]:checked");
    var severityList = [];
    for (var i = 0; i < checkboxes.length; i++) {
      severityList.push(checkboxes[i].name.replace("sev_", ""));
    }
    var severities = severityList.length ? severityList.join(",") : "ERROR,WARN,INFO,DEBUG";

    var fd = new FormData();
    fd.append("file", fileInput.files[0]);
    fd.append("severities", severities);

    setProgress("Uploading file...", "15%");

    try {
      var res = await fetch("/api/upload", { method: "POST", body: fd });
      if (!res.ok) {
        var err = await res.json();
        throw new Error(err.detail || "Upload failed");
      }
      var data = await res.json();
      var jobId = data.job_id;
      setProgress("Analyzing logs with AI...", "35%");
      await pollUntilDone(jobId);
    } catch (err) {
      setProgress("Error: " + err.message, "100%", true);
      submitBtn.disabled = false;
      form.classList.remove("opacity-50", "pointer-events-none");
    }
  });
}

function setProgress(text, width, isError) {
  progressText.textContent = text;
  progressBar.style.width = width;
  if (isError) {
    progressBar.classList.remove("bg-blue-500");
    progressBar.classList.add("bg-red-500");
  }
}

function scheduleProgressUpdates() {
  progressTimers.push(setTimeout(function () {
    setProgress("Parsing log entries...", "45%");
  }, 3000));

  progressTimers.push(setTimeout(function () {
    setProgress("Extracting error patterns...", "60%");
  }, 7000));

  progressTimers.push(setTimeout(function () {
    setProgress("Running root cause analysis...", "75%");
  }, 12000));

  progressTimers.push(setTimeout(function () {
    setProgress("Generating recommendations...", "88%");
  }, 18000));
}

function cancelProgressUpdates() {
  for (var i = 0; i < progressTimers.length; i++) {
    clearTimeout(progressTimers[i]);
  }
  progressTimers = [];
}

async function pollUntilDone(jobId) {
  scheduleProgressUpdates();

  try {
    while (true) {
      await sleep(2500);
      var res = await fetch("/api/analysis/" + jobId);
      if (res.status === 202) continue;

      cancelProgressUpdates();

      if (!res.ok) {
        var err = await res.json();
        throw new Error(err.detail || "Analysis failed");
      }

      setProgress("Complete! Loading dashboard...", "100%");
      await sleep(500);
      window.location.href = "/dashboard/" + jobId;
      return;
    }
  } catch (err) {
    cancelProgressUpdates();
    throw err;
  }
}

function sleep(ms) {
  return new Promise(function (resolve) {
    setTimeout(resolve, ms);
  });
}
