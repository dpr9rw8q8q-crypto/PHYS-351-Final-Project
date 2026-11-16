const form = document.querySelector("#order");
const submit = document.querySelector("#submit");
const status = document.querySelector("#status");
let resultsFile;
let loadingFile = true;
let rememberFile = false;

function storedFile(mode, action) {
  return new Promise((resolve, reject) => {
    const open = indexedDB.open("storm-stop-boba", 1);
    open.onupgradeneeded = () => open.result.createObjectStore("files");
    open.onerror = () => reject(open.error);
    open.onsuccess = () => {
      const db = open.result;
      try {
        const tx = db.transaction("files", mode);
        const request = action(tx.objectStore("files"));
        tx.oncomplete = () => {
          db.close();
          resolve(request.result);
        };
        tx.onabort = () => {
          db.close();
          reject(tx.error);
        };
      } catch (error) {
        db.close();
        reject(error);
      }
    };
  });
}

async function saveOrder(order) {
  if (!window.showOpenFilePicker) {
    throw new Error("Open this localhost page in Chrome or Edge to link results.txt.");
  }

  if (!resultsFile) {
    status.textContent = "Select web-interface/results.txt to save your first order.";
    const [file] = await window.showOpenFilePicker({
      id: "tea-order-results",
      types: [{ description: "Results text file", accept: { "text/plain": [".txt"] } }],
      excludeAcceptAllOption: true,
    });
    if (file.name !== "results.txt") {
      throw new Error("Please select the results.txt file inside web-interface.");
    }
    resultsFile = file;
    rememberFile = true;
  }

  if (await resultsFile.requestPermission({ mode: "readwrite" }) !== "granted") {
    throw new Error("Allow write access to results.txt to save your order.");
  }

  if (rememberFile) {
    await storedFile("readwrite", store => store.put(resultsFile, "results"))
      .then(() => { rememberFile = false; })
      .catch(() => {});
  }

  let file;
  try {
    file = await resultsFile.getFile();
  } catch (error) {
    if (error.name !== "NotFoundError") throw error;
    resultsFile = undefined;
    await storedFile("readwrite", store => store.delete("results")).catch(() => {});
    throw new Error("The linked results.txt moved or was deleted. Submit again to select it.");
  }
  const needsNewline = file.size > 0 && await file.slice(-1).text() !== "\n";
  const writer = await resultsFile.createWritable({ keepExistingData: true, mode: "exclusive" });
  try {
    await writer.seek(file.size);
    await writer.write((needsNewline ? "\n" : "") + JSON.stringify(order) + "\n");
    await writer.close();
  } catch (error) {
    await writer.abort().catch(() => {});
    throw error;
  }
}

function selected(name) {
  return form.querySelector(`input[name="${name}"]:checked`);
}

function updateSummary() {
  document.querySelector("#summary-tea").textContent = selected("tea").dataset.label;
  document.querySelector("#summary-options").textContent =
    `${selected("sugar_percent").value}% sugar · ${selected("ice").dataset.label} · ${selected("boba").value === "yes" ? "Boba pearls" : "No pearls"}`;
}

form.addEventListener("change", () => {
  updateSummary();
  status.textContent = "";
  submit.disabled = loadingFile;
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (loadingFile || submit.disabled) return;
  const order = {
    tea: selected("tea").value,
    sugar_percent: Number(selected("sugar_percent").value),
    ice: selected("ice").value,
    boba: selected("boba").value === "yes",
  };
  const inputs = form.querySelectorAll("input");
  inputs.forEach(input => input.disabled = true);
  submit.disabled = true;
  status.dataset.kind = "";
  status.textContent = "Saving your order…";

  try {
    await saveOrder(order);
    status.dataset.kind = "success";
    status.textContent = "Order saved! Change a selection to submit another cup.";
    // Changing any selection or starting a new order re-enables submission.
    const another = document.createElement("a");
    another.href = "#menu";
    another.textContent = " Start another order";
    another.style.color = "inherit";
    another.addEventListener("click", () => {
      form.reset();
      updateSummary();
      submit.disabled = false;
      status.textContent = "";
      form.querySelector('input[name="tea"]:checked').focus();
    });
    status.append(another);
  } catch (error) {
    status.dataset.kind = error.name === "AbortError" ? "" : "error";
    status.textContent = error.name === "AbortError"
      ? "No order was saved. Submit again when you’re ready to select results.txt."
      : error.message || "Couldn’t save the order. Please try again.";
    submit.disabled = false;
  } finally {
    inputs.forEach(input => input.disabled = false);
  }
});

updateSummary();

// Load the handle before the click so the browser's permission prompt can use that click.
submit.disabled = true;
storedFile("readonly", store => store.get("results"))
  .then(file => { resultsFile = file; })
  .catch(() => {})
  .finally(() => {
    loadingFile = false;
    submit.disabled = false;
  });
