// 1. Page elements and session token

const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
const messages = document.getElementById("messages");
const questionInput = document.getElementById("question");
const chatForm = document.getElementById("chat-form");
const sendButton = document.getElementById("send-button");

// 2. Add a message and optional source links

function addMessage(role, text, sources = []) {
    const article = document.createElement("article")
    article.className = `message ${role}`;

    if (role === "assistant") {
        const mark = document.createElement("div");
        mark.className = "message-mark";
        mark.setAttribute("aria-hidden", "true");
        mark.textContent = "F";
        article.append(mark);
    }

    const body = document.createElement("div");
    body.className = role === "assistant" ? "message-body" : "";

    const label = document.createElement("div");
    label.className = "message-label";
    label.textContent = role === "user" ? "You" : "Project mentor";

    const content = document.createElement("div");
    content.className = "message-text";
    content.textContent = text;
    body.append(label, content);
    article.append(body);

    if (sources.length) {
        const sourceArea = document.createElement("div");
        sourceArea.className = "sources";

        sources.forEach((source, index) => {
            const item = document.createElement("div");
            const link = document.createElement("a");
            link.href = source.url;
            link.target = "_blank";
            link.rel = "noopener noreferrer";
            link.textContent = `[${index + 1}] ${source.title}`;

            const snippet = document.createElement("small");
            snippet.textContent = source.snippet || "";
            item.append(link, snippet);
            sourceArea.append(item);
        });

        body.append(sourceArea);
    }

    messages.append(article);
    article.scrollIntoView({behavior: "smooth", block: "nearest"});
}

// 3. Restore this session's history after refresh

async function loadHistory() {
    const response = await fetch("/api/history");
    const data = await response.json();
    messages.replaceChildren();

    if (!data.history.length) {
        addMessage(
            "assistant",
            "Hi! Tell me what you are building, or ask about project planning, "
            + "concepts, algorithms, data, training, evaluation, debugging, "
            + "deployment, documentation, or responsible AI."
        );
        return;
    }

    data.history.forEach((message) => {
        addMessage(message.role, message.content, message.sources || []);
    });
}

// 4. Send questions to flask

chatForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const question = questionInput.value.trim();
    if (!question) return;

    addMessage("user", question);
    questionInput.value = "";
    sendButton.disabled = true;
    sendButton.textContent = "Thinking...";

    try{
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRF-Token": csrfToken,
        },
        body: JSON.stringify({
            message: question,
            search: document.getElementById("search-enabled").checked,
        }),
    });

      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Request failed.");
      addMessage("assistant", data.answer, data.sources || []);
    } catch(error) {
      console.error("Chat request failed:", error);
      addMessage(
        "assistant",
        "I couldn't complete that request. Check that Flask and Ollama are "
        + "running, then try again."
      );
    } finally {
        sendButton.disabled = false;
        sendButton.textContent = "Send";
        questionInput.focus();
    }
});

// 5. Start a fresh conversation in the current session

document.getElementById("clear-button").addEventListener("click", async () => {
    if (!confirm("Clear this session's conversation?")) return;

    const response = await fetch("/api/reset", {
        method: "POST",
        headers: { "X-CSRF-Token": csrfToken }
    });

    if (response.ok) await loadHistory();
});

// 6. Suggested prompts

document.querySelectorAll("[data-prompt]").forEach((button) => {
    button.addEventListener("click", () => {
        questionInput.value = button.dataset.prompt;
        questionInput.focus();
    });
});

// 7. Toggle the navigation and project context panels

const menuToggle = document.getElementById("menuToggle");
const contextToggle = document.getElementById("contextToggle");
const appShell = document.querySelector(".app-shell");

menuToggle.addEventListener("click", () => {
    const open = appShell.classList.toggle("show-left");
    menuToggle.setAttribute("aria-expanded", String(open));
});

document.getElementById("sidebarClose").addEventListener("click", () => {
    appShell.classList.remove("show-left");
    menuToggle.setAttribute("aria-expanded", "false");
    menuToggle.focus();
});

contextToggle.addEventListener("click", () => {
    const open = appShell.classList.toggle("show-right");
    contextToggle.setAttribute("aria-expanded", String(open));
});

document.getElementById("contextClose").addEventListener("click", () => {
    appShell.classList.remove("show-right");
    contextToggle.setAttribute("aria-expanded", "false");
    contextToggle.focus();
});

// 8. Keyboard shortcut and initial load

questionInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        chatForm.requestSubmit();
    }
});

try {
    await loadHistory();
} catch (error) {
    console.error("Could not load session history:", error);
    addMessage("assistant", "I couldn't load the conversation. refresh the page to try again.");
}
