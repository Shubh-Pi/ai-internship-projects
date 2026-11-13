"use strict";

const $ = (selector) => document.querySelector(selector);

const form = $("#generator-form");
const typeSelect = $("#content-type");
const topic = $("#topic");
const state = {
  currentDraft: "",
  pendingDraft: "",
  settings: null,
  controller: null,
  busy: false,
};

function countText(text) {
  return {
    words: (text.trim().match(/\S+/g) || []).length,
    characters: Array.from(text).length,
  };
}

function updateCounts(text, wordElement, characterElement) {
  const count = countText(text);
  wordElement.textContent = count.words;
  characterElement.textContent = count.characters;
}

function showMessage(message, isError = false) {
  $("#toast").textContent = message;
  $("#toast").classList.toggle("error", isError);
}

function setBusy(busy) {
  state.busy = busy;
  $("#generate-button").hidden = busy;
  $("#stop-button").hidden = !busy;
  $("#regenerate-button").disabled = busy;
  $("#refine-button").disabled = busy;
  document.querySelectorAll(".chip").forEach((button) => {
    button.disabled = busy;
  });
  $("#draft-state").textContent = busy ? "Writing…" : (state.currentDraft ? "Draft ready" : "Waiting for a topic");
  if (busy) {
    showMessage("Your local model is writing. The first run can take longer while it warms up.");
  }
}

function generationSettings() {
  return {
    contentType: typeSelect.value,
    topic: topic.value.trim(),
    tone: $("#tone").value,
    length: $("#length").value,
    audience: $("#audience").value.trim(),
    keyPoints: $("#key-points").value.trim(),
    platform: $("#platform").value,
    callToAction: $("#call-to-action").checked,
  };
}

function showCurrentDraft(text, durationMs = null) {
  state.currentDraft = text;
  state.pendingDraft = "";
  $("#empty-state").hidden = true;
  $("#draft-card").hidden = false;
  $("#draft-text").textContent = text;
  $("#preview").hidden = true;
  $("#refine-tools").hidden = false;
  $("#generation-time").textContent = durationMs ? `· ${(durationMs / 1000).toFixed(1)}s` : "";
  updateCounts(text, $("#word-count"), $("#character-count"));
  $("#draft-state").textContent = "Draft ready";
}

function showPreview(text) {
  state.pendingDraft = text;
  $("#preview").hidden = false;
  $("#preview-text").textContent = text;
  $("#apply-button").disabled = !text.trim();
  updateCounts(text, $("#preview-words"), $("#preview-characters"));
}

function parseFrame(frame) {
  let eventName = "message";
  const data = [];

  for (const line of frame.replaceAll("\r", "").split("\n")) {
    if (line.startsWith("event:")) eventName = line.slice(6).trim();
    if (line.startsWith("data:")) data.push(line.slice(5).trimStart());
  }

  if (!data.length) return null;
  return { eventName, data: JSON.parse(data.join("\n")) };
}

async function runStream(url, payload, preserveDraft=false) {
  if (state.busy) return;

  const previousDraft = preserveDraft ? state.currentDraft : "";
  let generated = "";
  let durationMs = null;
  let finished = false;

  state.controller = new AbortController();
  setBusy(true);
  $("#form-error").hidden = true;
  showMessage("");

  if (!previousDraft) {
    state.currentDraft = "";
    state.pendingDraft = "";
    $("#preview").hidden = true;
    $("#refine-tools").hidden = true;
    $("#generation-time").textContent = "";
  }

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Accept": "text/event-stream" },
      body: JSON.stringify(payload),
      signal: state.controller.signal,
    });

    if (!response.ok) {
      let body = {};
      try { body = await response.json(); } catch { /* use the general message */ }
      throw new Error(body.error?.message || "The request could not be completed.");
    }
    if (!response.body) throw new Error("This browser cannot read the streamed response.");

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      let boundary;

      while ((boundary = buffer.indexOf("\n\n")) >= 0) {
        const frame = buffer.slice(0, boundary);
        buffer = buffer.slice(boundary + 2);
        const parsed = parseFrame(frame);
        if (!parsed) continue;

        if (parsed.eventName === "token") {
          generated += parsed.data.text || "";
          if (previousDraft) {
            showPreview(generated);
          } else {
            $("#draft-text").textContent = generated;
            updateCounts(generated, $("#word-count"), $("#character-count"));
          }
        } else if (parsed.eventName === "done") {
          finished = true;
          durationMs = parsed.data.durationMs || null;
        } else if (parsed.eventName === "error") {
          throw new Error(parsed.data.message || "Generation failed.");
        }
      }
    }

    if (!finished) throw new Error("The generation ended before the draft was complete.");

    if (previousDraft) {
      showPreview(generated);
      showMessage("Review the new version, then choose whether to replace your draft.");
    } else {
      showCurrentDraft(generated, durationMs);
      showMessage("Draft complete. You can refine it or copy it.");
    }
  } catch (error) {
    const stopped = error.name === "AbortError";

    if (generated.trim()) {
      if (previousDraft) showPreview(generated);
      else showCurrentDraft(generated);
    } else if (!previousDraft) {
      $("#draft-card").hidden = true;
      $("#empty-state").hidden = false;
    }

    showMessage(stopped ? "Generation stopped." : (error.message || "Generation failed."), !stopped);
  } finally {
    state.controller = null;
    setBusy(false);
  }
}

async function checkModel() {
  try {
    const response = await fetch("/api/health");
    const data = await response.json();

    if (data.status === "ready") {
      $("#model-status").classList.add("ready");
      $("#model-status").classList.remove("error");
      $("#model-status-text").textContent = `${data.model} · local model ready`;
    } else {
      $("#model-status").classList.add("error");
      $("#model-status-text").textContent = data.message || "Local model unavailable";
    }
  } catch {
    $("#model-status").classList.add("error");
    $("#model-status-text").textContent = "Could not reach the local model";
  }
}

function startRefine(instruction) {
  if (!state.currentDraft || !instruction.trim()) return;

  runStream("/api/refine", {
    contentType: state.settings?.contentType || typeSelect.value,
    tone: state.settings?.tone || $("#tone").value,
    platform: state.settings?.platform || $("#platform").value,
    draft: state.currentDraft,
    instruction: instruction.trim(),
    }, true);
 } 

form.addEventListener("submit", (event) => {
  event.preventDefault();

  const settings = generationSettings();
  if (!settings.topic) {
    $("#form-error").textContent = "Add a topic before generating a draft.";
    $("#form-error").hidden = false;
    topic.focus();
    return;
  }

  state.settings = settings;
  runStream("/api/generate", settings);
});

$("#regenerate-button").addEventListener("click", () => {
  if (state.settings) runStream("/api/generate", state.settings, true);
});

$("#refine-form").addEventListener("submit", (event) => {
  event.preventDefault();
  startRefine($("#refine-instruction").value);
  $("#refine-instruction").value = "";
});

document.querySelectorAll("[data-refine]").forEach((button) => {
  button.addEventListener("click", () => startRefine(button.dataset.refine));
});

$("#apply-button").addEventListener("click", () => {
  if (state.pendingDraft.trim()) {
    showCurrentDraft(state.pendingDraft);
    showMessage("Revised draft applied.");
  }
});

$("#discard-button").addEventListener("click", () => {
  state.pendingDraft = "";
  $("#preview").hidden = true;
  showMessage("Kept your current draft.");
});

$("#copy-button").addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(state.currentDraft);
    showMessage("Copied to clipboard.");
  } catch {
    showMessage("Clipboard access was blocked by the browser.", true);
  }
});

$("#stop-button").addEventListener("click", () => state.controller?.abort());

typeSelect.addEventListener("change", () => {
  const isCaption = typeSelect.value === "caption";
  $("#platform-field").hidden = !isCaption;
  $("#cta-field").hidden = !isCaption;
});

topic.addEventListener("input", () => {
  $("#topic-count").textContent = `${topic.value.length} / 240`;
});

document.querySelectorAll("[data-topic]").forEach((button) => {
  button.addEventListener("click", () => {
    topic.value = button.dataset.topic;
    topic.dispatchEvent(new Event("input"));
    topic.focus();
  });
});

checkModel();