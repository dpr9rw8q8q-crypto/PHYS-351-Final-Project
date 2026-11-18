const form = document.querySelector("#order");
const submit = document.querySelector("#submit");
const status = document.querySelector("#status");
async function saveOrder(order) {
  const response = await fetch("/api/orders", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(order),
  });
  if (!response.ok) {
    throw new Error("Couldn’t save the order. Check the Pi terminal and try again.");
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
  submit.disabled = false;
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (submit.disabled) return;
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
    status.dataset.kind = "error";
    status.textContent = error.message || "Couldn’t save the order. Please try again.";
    submit.disabled = false;
  } finally {
    inputs.forEach(input => input.disabled = false);
  }
});

updateSummary();

submit.disabled = false;
