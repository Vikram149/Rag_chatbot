// ==================================================
// Application state
// ==================================================

const state = {
    documents: [],
    chats: [],
    retrievalRuns: [],
    currentChatId: null,
    selectedDocumentIds: [],
    pendingDelete: null,
    isSending: false,
    activeRequestController: null,
    chatSearchQuery: "",
};


// ==================================================
// Elements
// ==================================================

const navigationItems =
    document.querySelectorAll(".navigation-item");

const applicationViews =
    document.querySelectorAll(".application-view");

const sidebar = document.getElementById("sidebar");
const openSidebarButton =
    document.getElementById("open-sidebar-button");
const closeSidebarButton =
    document.getElementById("close-sidebar-button");
const collapseSidebarButton =
    document.getElementById(
        "collapse-sidebar-button"
    );

const expandSidebarButton =
    document.getElementById(
        "expand-sidebar-button"
    );
const newChatButton =
    document.getElementById("new-chat-button");
const chatHistoryList =
    document.getElementById("chat-history-list");
const chatSearchInput =
    document.getElementById("chat-search-input");

const currentChatTitle =
    document.getElementById("current-chat-title");
const chatMessages =
    document.getElementById("chat-messages");
const chatEmptyState =
    document.getElementById("chat-empty-state");
const chatForm =
    document.getElementById("chat-form");
const chatInput =
    document.getElementById("chat-input");
const sendButton =
    document.getElementById("send-button");

const stopButton =
document.getElementById("stop-button");

const selectedDocumentsSummary =
    document.getElementById(
        "selected-documents-summary"
    );

const selectDocumentsButton =
    document.getElementById(
        "select-documents-button"
    );

const fileInput =
    document.getElementById("file-input");
const uploadDropZone =
    document.getElementById("upload-drop-zone");
const uploadQueue =
    document.getElementById("upload-queue");

const documentsUploadButton =
    document.getElementById(
        "documents-upload-button"
    );

const refreshDocumentsButton =
    document.getElementById(
        "refresh-documents-button"
    );

const documentSearchInput =
    document.getElementById(
        "document-search-input"
    );

const documentsTableBody =
    document.getElementById(
        "documents-table-body"
    );

const totalDocumentsStat =
    document.getElementById(
        "total-documents-stat"
    );

const readyDocumentsStat =
    document.getElementById(
        "ready-documents-stat"
    );

const processingDocumentsStat =
    document.getElementById(
        "processing-documents-stat"
    );

const failedDocumentsStat =
    document.getElementById(
        "failed-documents-stat"
    );

const totalChunksStat =
    document.getElementById(
        "total-chunks-stat"
    );

const refreshAnalyticsButton =
    document.getElementById(
        "refresh-analytics-button"
    );

const analyticsSearchInput =
    document.getElementById(
        "analytics-search-input"
    );

const analyticsRunsTableBody =
    document.getElementById(
        "analytics-runs-table-body"
    );

const analyticsTotalRuns =
    document.getElementById(
        "analytics-total-runs"
    );

const analyticsTotalChunks =
    document.getElementById(
        "analytics-total-chunks"
    );

const analyticsAverageChunks =
    document.getElementById(
        "analytics-average-chunks"
    );

const analyticsAverageSimilarity =
    document.getElementById(
        "analytics-average-similarity"
    );

const analyticsClaudeCalls =
    document.getElementById(
        "analytics-claude-calls"
    );

const retrievalDetailsPanel =
    document.getElementById(
        "retrieval-details-panel"
    );

const retrievalDetailsTitle =
    document.getElementById(
        "retrieval-details-title"
    );

const retrievalRunSummary =
    document.getElementById(
        "retrieval-run-summary"
    );

const retrievalChunksList =
    document.getElementById(
        "retrieval-chunks-list"
    );

const closeRetrievalDetailsButton =
    document.getElementById(
        "close-retrieval-details-button"
    );

const documentSelectionModal =
    document.getElementById(
        "document-selection-modal"
    );

const documentSelectionList =
    document.getElementById(
        "document-selection-list"
    );

const closeDocumentModalButton =
    document.getElementById(
        "close-document-modal-button"
    );

const selectAllDocumentsButton =
    document.getElementById(
        "select-all-documents-button"
    );

const saveDocumentSelectionButton =
    document.getElementById(
        "save-document-selection-button"
    );

const confirmationModal =
    document.getElementById(
        "confirmation-modal"
    );

const confirmationMessage =
    document.getElementById(
        "confirmation-message"
    );

const cancelConfirmationButton =
    document.getElementById(
        "cancel-confirmation-button"
    );

const confirmDeleteButton =
    document.getElementById(
        "confirm-delete-button"
    );

const loadingOverlay =
    document.getElementById("loading-overlay");

const loadingMessage =
    document.getElementById("loading-message");

const toast =
    document.getElementById("toast");
const themeToggleButton =
    document.getElementById(
        "theme-toggle-button"
    );

const themeToggleIcon =
    document.getElementById(
        "theme-toggle-icon"
    );

const themeToggleLabel =
    document.getElementById(
        "theme-toggle-label"
    );

const documentPreviewPanel =
    document.getElementById(
        "document-preview-panel"
    );

const documentPreviewTitle =
    document.getElementById(
        "document-preview-title"
    );

const documentPreviewFrame =
    document.getElementById(
        "document-preview-frame"
    );

const closePreviewButton =
    document.getElementById(
        "close-preview-button"
    );

const sidebarUsername =
    document.getElementById(
        "sidebar-username"
    );


const openPreviewTabButton =
    document.getElementById(
        "open-preview-tab-button"
    );

let currentPreviewUrl = "";

const replaceDocumentInput =
    document.getElementById(
        "replace-document-input"
    );

let documentIdBeingReplaced = null;

function openDocumentPreview(
    documentId,
    pageNumber = null
) {
    const selectedDocument =
        state.documents.find(
            (document) =>
                Number(document.id) ===
                Number(documentId)
        );

    if (!selectedDocument) {
        showToast(
            "Document information was not found.",
            "error"
        );

        return;
    }

    let previewUrl =
        `/api/documents/${documentId}/preview`;

    if (pageNumber) {
        previewUrl +=
            `#page=${pageNumber}&zoom=page-width`;
    }

    currentPreviewUrl = previewUrl;

    documentPreviewTitle.textContent =
        selectedDocument.filename;

    documentPreviewFrame.src =
        previewUrl;

    documentPreviewPanel.setAttribute(
        "aria-hidden",
        "false"
    );

    document.body.classList.add(
        "document-preview-open"
    );
}


function closeDocumentPreview() {
    document.body.classList.remove(
        "document-preview-open"
    );

    documentPreviewPanel.setAttribute(
        "aria-hidden",
        "true"
    );

    documentPreviewFrame.src =
        "about:blank";

    currentPreviewUrl = "";
}

chatMessages.addEventListener(
    "click",
    (event) => {
        const previewButton =
            event.target.closest(
                ".source-preview-button"
            );

        if (!previewButton) {
            return;
        }

        openDocumentPreview(
            Number(
                previewButton.dataset.documentId
            ),
            Number(
                previewButton.dataset.pageNumber
            ) || null
        );
    }
);
closePreviewButton.addEventListener(
    "click",
    closeDocumentPreview
);


openPreviewTabButton.addEventListener(
    "click",
    () => {
        if (currentPreviewUrl) {
            window.open(
                currentPreviewUrl,
                "_blank",
                "noopener"
            );
        }
    }
);

const exportTextButton =
    document.getElementById(
        "export-text-button"
    );

const exportPdfButton =
    document.getElementById(
        "export-pdf-button"
    );

const logoutButton =
    document.getElementById("logoutButton");

if (logoutButton) {
    logoutButton.addEventListener(
        "click",
        async () => {
            try {
                const response = await fetch(
                    "/api/auth/logout",
                    {
                        method: "POST",
                        credentials: "same-origin"
                    }
                );

                if (!response.ok) {
                    throw new Error(
                        "Unable to log out."
                    );
                }

                window.location.href = "/login";
            } catch (error) {
                alert(error.message);
            }
        }
    );
}
// ==================================================
// API helper
// ==================================================

async function apiRequest(url, options = {}) {
    const response = await fetch(url, options);

    let data = {};

    try {
        data = await response.json();
    } catch {
        data = {};
    }

    if (!response.ok) {
        throw new Error(
            data.detail ||
            "Something went wrong."
        );
    }

    return data;
}


// ==================================================
// General helpers
// ==================================================

function escapeHtml(value) {
    const element = document.createElement("div");
    element.textContent = value ?? "";
    return element.innerHTML;
}


function formatBytes(bytes) {
    const number = Number(bytes || 0);

    if (number === 0) {
        return "0 B";
    }

    const units = [
        "B",
        "KB",
        "MB",
        "GB",
    ];

    const unitIndex = Math.floor(
        Math.log(number) / Math.log(1024)
    );

    const size = number / Math.pow(
        1024,
        unitIndex
    );

    return `${size.toFixed(
        unitIndex === 0 ? 0 : 1
    )} ${units[unitIndex]}`;
}


function formatDate(dateValue) {
    if (!dateValue) {
        return "-";
    }

    return new Date(dateValue).toLocaleString(
        [],
        {
            month: "short",
            day: "numeric",
            year: "numeric",
            hour: "numeric",
            minute: "2-digit",
        }
    );
}


function showToast(message, isError = false) {
    toast.textContent = message;

    toast.classList.toggle(
        "error",
        isError
    );

    toast.classList.remove("hidden");

    window.clearTimeout(
        showToast.timeoutId
    );

    showToast.timeoutId = window.setTimeout(
        () => {
            toast.classList.add("hidden");
        },
        3500
    );
}


function showLoading(message = "Processing...") {
    loadingMessage.textContent = message;
    loadingOverlay.classList.remove("hidden");
}


function hideLoading() {
    loadingOverlay.classList.add("hidden");
}


// ==================================================
// Navigation
// ==================================================

function showView(viewName) {
    applicationViews.forEach((view) => {
        view.classList.toggle(
            "active",
            view.id === `${viewName}-view`
        );
    });

    navigationItems.forEach((item) => {
        item.classList.toggle(
            "active",
            item.dataset.view === viewName
        );
    });

    sidebar.classList.remove("open");

    if (
        viewName === "documents" ||
        viewName === "upload"
    ) {
        loadDocuments();
    }

    if (viewName === "analytics") {
        loadRetrievalAnalytics();
    }
}


navigationItems.forEach((item) => {
    item.addEventListener("click", () => {
        showView(item.dataset.view);
    });
});


documentsUploadButton.addEventListener(
    "click",
    () => {
        showView("upload");
    }
);


openSidebarButton.addEventListener(
    "click",
    () => {
        sidebar.classList.add("open");
    }
);


closeSidebarButton.addEventListener(
    "click",
    () => {
        sidebar.classList.remove("open");
    }
);

function setSidebarCollapsed(collapsed) {
    document.body.classList.toggle(
        "sidebar-collapsed",
        collapsed
    );

    localStorage.setItem(
        "sidebar-collapsed",
        String(collapsed)
    );
}


collapseSidebarButton.addEventListener(
    "click",
    () => {
        setSidebarCollapsed(true);
    }
);


expandSidebarButton.addEventListener(
    "click",
    () => {
        setSidebarCollapsed(false);
    }
);


if (
    localStorage.getItem(
        "sidebar-collapsed"
    ) === "true" &&
    window.innerWidth > 780
) {
    setSidebarCollapsed(true);
}

function applyTheme(theme) {
    document.documentElement.dataset.theme =
        theme;

    const isDark = theme === "dark";

    themeToggleIcon.textContent =
        isDark ? "☀" : "☾";

    themeToggleLabel.textContent =
        isDark ? "Light mode" : "Dark mode";

    themeToggleButton.setAttribute(
        "aria-pressed",
        String(isDark)
    );

    localStorage.setItem(
        "application-theme",
        theme
    );
}


themeToggleButton.addEventListener(
    "click",
    () => {
        const currentTheme =
            document.documentElement.dataset.theme;

        applyTheme(
            currentTheme === "dark"
                ? "light"
                : "dark"
        );
    }
);


applyTheme(
    localStorage.getItem(
        "application-theme"
    ) || "light"
);
// ==================================================
// Documents
// ==================================================

async function loadDocuments() {
    try {
        const data = await apiRequest(
            "/api/documents"
        );

        state.documents =
            data.documents || [];

        renderDocuments();
        renderDocumentStatistics();
        updateSelectedDocumentsSummary();

    } catch (error) {
        showToast(error.message, true);
    }
}


function renderDocumentStatistics() {
    const documents = state.documents;

    totalDocumentsStat.textContent =
        documents.length;

    readyDocumentsStat.textContent =
        documents.filter(
            (document) =>
                document.status === "ready"
        ).length;

    processingDocumentsStat.textContent =
        documents.filter(
            (document) =>
                document.status === "processing"
        ).length;

    failedDocumentsStat.textContent =
        documents.filter(
            (document) =>
                document.status === "failed"
        ).length;

    totalChunksStat.textContent =
        documents.reduce(
            (total, document) =>
                total +
                Number(document.chunk_count || 0),
            0
        );
}


function renderDocuments() {
    const searchValue =
        documentSearchInput.value
            .trim()
            .toLowerCase();

    const filteredDocuments =
        state.documents.filter(
            (document) =>
                document.filename
                    .toLowerCase()
                    .includes(searchValue)
        );

    if (filteredDocuments.length === 0) {
        documentsTableBody.innerHTML = `
            <tr>
                <td
                    colspan="7"
                    class="table-empty-message"
                >
                    No documents found
                </td>
            </tr>
        `;

        return;
    }

    documentsTableBody.innerHTML =
        filteredDocuments.map(
            (document) => `
                <tr>
                    <td
                        class="document-name-cell"
                        title="${escapeHtml(
                            document.filename
                        )}"
                    >
                        ${escapeHtml(
                            document.filename
                        )}
                    </td>

                    <td>
                        ${escapeHtml(
                            document.file_type.toUpperCase()
                        )}
                    </td>

                    <td>
                        <span
                            class="status-badge
                            status-${escapeHtml(
                                document.status
                            )}"
                        >
                            ${escapeHtml(
                                document.status
                            )}
                        </span>
                    </td>

                    <td>
                        ${document.chunk_count || 0}
                    </td>

                    <td>
                        ${formatBytes(
                            document.file_size_bytes
                        )}
                    </td>

                    <td>
                        ${formatDate(
                            document.uploaded_at
                        )}
                    </td>

                    <td class="actions-column">
                        <div class="document-actions">
    <button
        class="preview-document-button"
        type="button"
        data-document-id="${document.id}"
        title="Preview document"
        aria-label="Preview document"
    >
        👁
    </button>
    <button
        class="replace-document-button"
        type="button"
        data-document-id="${document.id}"
        data-document-name="${escapeHtml(
            document.filename
        )}"
        title="Replace document"
        aria-label="Replace document"
    >
        ↻
    </button>

    <button
        class="delete-document-button"
        type="button"
        data-document-id="${document.id}"
        data-document-name="${escapeHtml(
            document.filename
        )}"
        aria-label="Delete document"
        title="Delete document"
    >
        ×
    </button>
</div>
                    </td>
                </tr>
            `
        ).join("");
}


documentSearchInput.addEventListener(
    "input",
    renderDocuments
);


refreshDocumentsButton.addEventListener(
    "click",
    loadDocuments
);


documentsTableBody.addEventListener(
    "click",
    (event) => {
        const previewButton =
            event.target.closest(
                ".preview-document-button"
            );

        if (previewButton) {
            openDocumentPreview(
                Number(
                    previewButton.dataset.documentId
                )
            );

            return;
        }
        const replaceButton =
            event.target.closest(
                ".replace-document-button"
            );

        if (replaceButton) {
            documentIdBeingReplaced = Number(
                replaceButton.dataset.documentId
            );

            replaceDocumentInput.value = "";
            replaceDocumentInput.click();

            return;
        }

        const deleteButton =
            event.target.closest(
                ".delete-document-button"
            );

        if (!deleteButton) {
            return;
        }

        openDeleteConfirmation({
            type: "document",
            id: Number(
                deleteButton.dataset.documentId
            ),
            name:
                deleteButton.dataset.documentName,
        });
    }
);

function exportCurrentChat(format) {
    if (!state.currentChatId) {
        showToast(
            "Start or select a chat before exporting.",
            "error"
        );

        return;
    }

    window.location.href =
        `/api/chats/${state.currentChatId}/export/${format}`;
}


exportTextButton.addEventListener(
    "click",
    () => exportCurrentChat("text")
);


exportPdfButton.addEventListener(
    "click",
    () => exportCurrentChat("pdf")
);


// ==================================================
// Document upload
// ==================================================

uploadDropZone.addEventListener(
    "click",
    () => {
        fileInput.click();
    }
);


fileInput.addEventListener(
    "change",
    () => {
        uploadFiles(
            Array.from(fileInput.files)
        );

        fileInput.value = "";
    }
);


[
    "dragenter",
    "dragover",
].forEach((eventName) => {
    uploadDropZone.addEventListener(
        eventName,
        (event) => {
            event.preventDefault();

            uploadDropZone.classList.add(
                "dragging"
            );
        }
    );
});


[
    "dragleave",
    "drop",
].forEach((eventName) => {
    uploadDropZone.addEventListener(
        eventName,
        (event) => {
            event.preventDefault();

            uploadDropZone.classList.remove(
                "dragging"
            );
        }
    );
});


uploadDropZone.addEventListener(
    "drop",
    (event) => {
        const files = Array.from(
            event.dataTransfer.files
        );

        uploadFiles(files);
    }
);


function createUploadQueueItem(file) {
    const item = document.createElement("div");

    item.className = "upload-queue-item";

    item.innerHTML = `
        <div class="upload-file-information">
            <span class="upload-file-name">
                ${escapeHtml(file.name)}
            </span>

            <span class="upload-file-status">
                Waiting to upload ·
                ${formatBytes(file.size)}
            </span>
        </div>

        <span class="status-badge status-processing">
            Waiting
        </span>
    `;

    uploadQueue.prepend(item);

    return item;
}


function updateUploadQueueItem(
    item,
    status,
    message
) {
    const statusText = item.querySelector(
        ".upload-file-status"
    );

    const badge = item.querySelector(
        ".status-badge"
    );

    statusText.textContent = message;
    badge.textContent = status;

    badge.className =
        `status-badge status-${status}`;
}


async function uploadFiles(files) {
    if (!files.length) {
        return;
    }

    for (const file of files) {
        const queueItem =
            createUploadQueueItem(file);

        updateUploadQueueItem(
            queueItem,
            "processing",
            "Uploading and generating embeddings..."
        );

        const formData = new FormData();
        formData.append("file", file);

        try {
            await apiRequest(
                "/api/documents/upload",
                {
                    method: "POST",
                    body: formData,
                }
            );

            updateUploadQueueItem(
                queueItem,
                "ready",
                "Upload and embedding completed"
            );

            showToast(
                `${file.name} uploaded successfully.`
            );

        } catch (error) {
            updateUploadQueueItem(
                queueItem,
                "failed",
                error.message
            );

            showToast(error.message, true);
        }
    }

    await loadDocuments();
}


// ==================================================
// Document selection
// ==================================================

function openDocumentSelectionModal() {
    const readyDocuments =
        state.documents.filter(
            (document) =>
                document.status === "ready"
        );

    if (readyDocuments.length === 0) {
        showToast(
            "Upload at least one document first.",
            true
        );

        return;
    }

    documentSelectionList.innerHTML =
        readyDocuments.map(
            (document) => {
                const isSelected =
                    state.selectedDocumentIds
                        .includes(document.id);

                return `
                    <label
                        class="document-selection-item"
                    >
                        <input
                            type="checkbox"
                            value="${document.id}"
                            ${isSelected
                                ? "checked"
                                : ""}
                        >

                        <span
                            class="document-selection-information"
                        >
                            <span
                                class="document-selection-name"
                            >
                                ${escapeHtml(
                                    document.filename
                                )}
                            </span>

                            <span
                                class="document-selection-detail"
                            >
                                ${document.chunk_count}
                                chunks ·
                                ${escapeHtml(
                                    document.file_type.toUpperCase()
                                )}
                            </span>
                        </span>
                    </label>
                `;
            }
        ).join("");

    documentSelectionModal.classList.remove(
        "hidden"
    );
}


function closeDocumentSelectionModal() {
    documentSelectionModal.classList.add(
        "hidden"
    );
}


selectDocumentsButton.addEventListener(
    "click",
    openDocumentSelectionModal
);


closeDocumentModalButton.addEventListener(
    "click",
    closeDocumentSelectionModal
);


selectAllDocumentsButton.addEventListener(
    "click",
    () => {
        const checkboxes =
            documentSelectionList.querySelectorAll(
                'input[type="checkbox"]'
            );

        const allSelected =
            Array.from(checkboxes).every(
                (checkbox) => checkbox.checked
            );

        checkboxes.forEach((checkbox) => {
            checkbox.checked = !allSelected;
        });

        selectAllDocumentsButton.textContent =
            allSelected
                ? "Select all"
                : "Clear all";
    }
);


saveDocumentSelectionButton.addEventListener(
    "click",
    () => {
        const selectedCheckboxes =
            documentSelectionList.querySelectorAll(
                'input[type="checkbox"]:checked'
            );

        const selectedIds =
            Array.from(selectedCheckboxes).map(
                (checkbox) =>
                    Number(checkbox.value)
            );

        if (selectedIds.length === 0) {
            showToast(
                "Select at least one document.",
                true
            );

            return;
        }

        state.selectedDocumentIds =
            selectedIds;

        updateSelectedDocumentsSummary();
        closeDocumentSelectionModal();

        showToast(
            "Document selection updated."
        );
    }
);


function updateSelectedDocumentsSummary() {
    const readyDocuments =
        state.documents.filter(
            (document) =>
                document.status === "ready"
        );

    if (readyDocuments.length === 0) {
        selectedDocumentsSummary.textContent =
            "No ready documents available";

        return;
    }

    if (
        state.selectedDocumentIds.length === 0 ||
        state.selectedDocumentIds.length ===
            readyDocuments.length
    ) {
        selectedDocumentsSummary.textContent =
            `Searching all ${readyDocuments.length} ready document(s)`;

        return;
    }

    const selectedNames =
        readyDocuments
            .filter((document) =>
                state.selectedDocumentIds
                    .includes(document.id)
            )
            .map((document) =>
                document.filename
            );

    selectedDocumentsSummary.textContent =
        `Searching: ${selectedNames.join(", ")}`;
}


// ==================================================
// Chats
// ==================================================

async function loadChats() {
    try {
        const data = await apiRequest(
            "/api/chats"
        );

        state.chats = data.chats || [];
        renderChatHistory();

    } catch (error) {
        showToast(error.message, true);
    }
}


function renderChatHistory() {
    if (state.chats.length === 0) {
        chatHistoryList.innerHTML = `
            <div class="sidebar-empty-message">
                No chats yet
            </div>
        `;

        return;
    }

    const normalizedQuery =
        state.chatSearchQuery
            .trim()
            .toLowerCase();

    const visibleChats = state.chats.filter(
        (chat) =>
            String(chat.title || "")
                .toLowerCase()
                .includes(normalizedQuery)
    );

    if (visibleChats.length === 0) {
        chatHistoryList.innerHTML = `
            <div class="sidebar-empty-message">
                No matching chats
            </div>
        `;

        return;
    }

    chatHistoryList.innerHTML =
        visibleChats.map(
            (chat) => `
                <div
                    class="chat-history-item
                    ${chat.id === state.currentChatId
                        ? "active"
                        : ""}"
                    data-chat-id="${chat.id}"
                    role="button"
                    tabindex="0"
                >
                    <span class="chat-history-title">
                        ${escapeHtml(chat.title)}
                    </span>

                    <div class="chat-actions">

                        <button
                            class="chat-menu-button"
                            type="button"
                            onclick="toggleChatMenu(event, ${chat.id})"
                            aria-label="Chat options"
                            title="Chat options"
                        >
                            ⋯
                        </button>

                        <div
                            id="chat-menu-${chat.id}"
                            class="chat-options-menu hidden"
                        >
                            <button
                                class="rename-menu-option"
                                type="button"
                                onclick="openRenameChat(event, ${chat.id})"
                            >
                                <span class="rename-pencil-icon">
                                    ✎
                                </span>

                                <span>Rename</span>
                            </button>

                            <div class="chat-menu-divider"></div>

                            <button
                                class="delete-chat-button delete-menu-option"
                                type="button"
                                data-chat-id="${chat.id}"
                            >
                                <span class="delete-menu-icon">
                                    ×
                                </span>

                                <span>Delete</span>
                            </button>
                        </div>

                    </div>
                </div>
            `
        ).join("");
}

chatHistoryList.addEventListener(
    "click",
    (event) => {
        const deleteButton =
            event.target.closest(
                ".delete-chat-button"
            );

        if (deleteButton) {
    event.stopPropagation();

    const chatId = Number(
        deleteButton.dataset.chatId
    );

    const chat = state.chats.find(
        (item) => item.id === chatId
    );

    openDeleteConfirmation({
        type: "chat",
        id: chatId,
        name: chat?.title || "Chat",
    });

    return;
}

        const chatItem =
            event.target.closest(
                ".chat-history-item"
            );

        if (chatItem) {
            openChat(
                Number(chatItem.dataset.chatId)
            );
        }
    }
);


async function createNewChat() {
    try {
        const readyDocumentIds =
            state.documents
                .filter(
                    (document) =>
                        document.status === "ready"
                )
                .map(
                    (document) => document.id
                );

        const data = await apiRequest(
            "/api/chats",
            {
                method: "POST",
                headers: {
                    "Content-Type":
                        "application/json",
                },
                body: JSON.stringify({
                    title: "New Chat",
                    document_ids:
                        readyDocumentIds,
                }),
            }
        );

        state.currentChatId = data.id;
        state.selectedDocumentIds =
            data.document_ids || [];

        currentChatTitle.textContent =
            data.title;

        clearChatMessages();
        updateSelectedDocumentsSummary();

        await loadChats();
        showView("chat");

        chatInput.focus();

    } catch (error) {
        showToast(error.message, true);
    }
}


async function openChat(
    chatId,
    scrollToAnswer = false
) {
    try {
        showLoading("Opening chat...");

        const data = await apiRequest(
            `/api/chats/${chatId}/messages`
        );

        state.currentChatId = chatId;
        state.selectedDocumentIds =
            data.document_ids || [];

        const chat = state.chats.find(
            (item) => item.id === chatId
        );

        currentChatTitle.textContent =
            chat?.title || "Chat";

        renderChatMessages(
            data.messages || []
        );

        updateSelectedDocumentsSummary();
        renderChatHistory();
        showView("chat");

        if (scrollToAnswer) {
            requestAnimationFrame(() => {
                const buttons =
                    document.querySelectorAll(
                        ".regenerate-answer-button"
                    );

                const lastButton =
                    buttons[buttons.length - 1];

                if (!lastButton) {
                    return;
                }

                const answerElement =
                    lastButton.closest(".message") ||
                    lastButton.closest(
                        ".assistant-message"
                    ) ||
                    lastButton.closest(
                        ".message-row"
                    ) ||
                    lastButton.parentElement
                        ?.parentElement;

                answerElement?.scrollIntoView({
                    behavior: "smooth",
                    block: "start",
                });
            });
        }

    } catch (error) {
        showToast(error.message, true);

    } finally {
        hideLoading();
    }
}

function clearChatMessages() {
    chatMessages.innerHTML = "";
    chatMessages.appendChild(chatEmptyState);
    chatEmptyState.classList.remove("hidden");
}


newChatButton.addEventListener(
    "click",
    createNewChat
);


chatSearchInput.addEventListener(
    "input",
    () => {
        state.chatSearchQuery =
            chatSearchInput.value;

        renderChatHistory();
    }
);

replaceDocumentInput.addEventListener(
    "change",
    async () => {
        const replacementFile =
            replaceDocumentInput.files[0];

        if (
            !replacementFile ||
            !documentIdBeingReplaced
        ) {
            return;
        }

        const selectedDocument =
            state.documents.find(
                (document) =>
                    Number(document.id) ===
                    documentIdBeingReplaced
            );

        const confirmed = window.confirm(
            `Replace "${selectedDocument?.filename || "this document"}" with "${replacementFile.name}"?`
        );

        if (!confirmed) {
            replaceDocumentInput.value = "";
            documentIdBeingReplaced = null;
            return;
        }

        const formData = new FormData();

        formData.append(
            "file",
            replacementFile
        );
        closeDocumentPreview();

        try {
            const response = await fetch(
                `/api/documents/${documentIdBeingReplaced}/replace`,
                {
                    method: "PUT",
                    body: formData,
                }
            );

            const result = await response.json();

            if (!response.ok) {
                throw new Error(
                    result.detail ||
                    "Document replacement failed."
                );
            }

            closeDocumentPreview();
            await loadDocuments();

            showToast(
                "Document replaced and processed successfully.",
                "success"
            );
        } catch (error) {
            showToast(
                error.message,
                "error"
            );
        } finally {
            replaceDocumentInput.value = "";
            documentIdBeingReplaced = null;
        }
    }
);


// ==================================================
// Markdown formatting
// ==================================================

function formatInlineMarkdown(text) {
    return text
        .replace(
            /`([^`]+)`/g,
            "<code>$1</code>"
        )
        .replace(
            /\*\*([^*]+)\*\*/g,
            "<strong>$1</strong>"
        );
}


function renderMarkdown(value) {
    const safeText = escapeHtml(value);
    const lines = safeText.split("\n");

    let html = "";
    let inUnorderedList = false;
    let inOrderedList = false;
    let inCodeBlock = false;

    for (const line of lines) {
        if (line.trim().startsWith("```")) {
            if (!inCodeBlock) {
                html += "<pre><code>";
                inCodeBlock = true;
            } else {
                html += "</code></pre>";
                inCodeBlock = false;
            }

            continue;
        }

        if (inCodeBlock) {
            html += `${line}\n`;
            continue;
        }

        if (!line.trim()) {
            continue;
        }
        
        if (/^\s*[-*]\s+/.test(line)) {
            if (!inUnorderedList) {
                html += "<ul>";
                inUnorderedList = true;
            }

            html += `<li>${
                formatInlineMarkdown(
                    line.replace(
                        /^\s*[-*]\s+/,
                        ""
                    )
                )
            }</li>`;

            continue;
        }

        if (/^\s*\d+\.\s+/.test(line)) {
            if (!inOrderedList) {
                html += "<ol>";
                inOrderedList = true;
            }

            html += `<li>${
                formatInlineMarkdown(
                    line.replace(
                        /^\s*\d+\.\s+/,
                        ""
                    )
                )
            }</li>`;

            continue;
        }

        if (inUnorderedList) {
            html += "</ul>";
            inUnorderedList = false;
        }

        if (inOrderedList) {
            html += "</ol>";
            inOrderedList = false;
        }

        if (!line.trim()) {
            continue;
        }

        if (line.startsWith("### ")) {
            html += `<h3>${
                formatInlineMarkdown(
                    line.substring(4)
                )
            }</h3>`;

        } else if (line.startsWith("## ")) {
            html += `<h2>${
                formatInlineMarkdown(
                    line.substring(3)
                )
            }</h2>`;

        } else if (line.startsWith("# ")) {
            html += `<h2>${
                formatInlineMarkdown(
                    line.substring(2)
                )
            }</h2>`;

        } else {
            html += `<p>${
                formatInlineMarkdown(line)
            }</p>`;
        }
    }

    if (inUnorderedList) {
        html += "</ul>";
    }

    if (inOrderedList) {
        html += "</ol>";
    }

    if (inCodeBlock) {
        html += "</code></pre>";
    }

    return html;
}


// ==================================================
// Chat messages
// ==================================================

function renderChatMessages(messages) {
    chatMessages.innerHTML = "";

    if (messages.length === 0) {
        chatMessages.appendChild(
            chatEmptyState
        );

        chatEmptyState.classList.remove(
            "hidden"
        );

        return;
    }

    chatEmptyState.classList.add("hidden");

    const lastAssistantIndex =
        messages.map(
            (message) => message.role
        ).lastIndexOf("assistant");

    let latestQuestion = "";

    messages.forEach((message, index) => {
        if (message.role === "user") {
            latestQuestion = message.content;
        }

        const messageElement = appendMessage(
            message.role,
            message.content,
            message.sources || []
        );

        if (
            message.role === "assistant" &&
            index === lastAssistantIndex
        ) {
            addAssistantTools(
                messageElement,
                latestQuestion,
                message.sources || []
            );
        }
    });

    scrollChatToBottom();
}


function appendMessage(
    role,
    content,
    sources = []
) {
    chatEmptyState.classList.add("hidden");

    if (
        chatEmptyState.parentElement ===
        chatMessages
    ) {
        chatEmptyState.remove();
    }

    const messageElement =
        document.createElement("article");

    messageElement.className =
        `message message-${role}`;

    const label =
        role === "user"
            ? "You"
            : "Assistant";

    messageElement.innerHTML = `
        <div class="message-label">
            ${label}
        </div>

        <div class="message-content">
            ${
                role === "assistant"
                    ? renderMarkdown(content)
                    : `<p>${escapeHtml(content)}</p>`
            }
        </div>
            <div class="message-actions">
                <button
                    class="copy-message-button"
                    type="button"
                    title="${
                        role === "user"
                            ? "Copy question"
                            : "Copy answer"
                    }"
                    aria-label="${
                        role === "user"
                            ? "Copy question"
                            : "Copy answer"
                    }"
                >
                    <svg
                        viewBox="0 0 24 24"
                        width="17"
                        height="17"
                        aria-hidden="true"
                    >
                        <rect
                            x="8"
                            y="8"
                            width="11"
                            height="11"
                            rx="2"
                            fill="none"
                            stroke="currentColor"
                            stroke-width="1.8"
                        ></rect>

                        <path
                            d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"
                            fill="none"
                            stroke="currentColor"
                            stroke-width="1.8"
                            stroke-linecap="round"
                        ></path>
                    </svg>
                </button>
            </div>
    `;
    const copyMessageButton =
    messageElement.querySelector(
        ".copy-message-button"
    );

copyMessageButton.addEventListener(
    "click",
    async () => {
        try {
            await navigator.clipboard.writeText(
                content
            );

            const originalIcon =
                copyMessageButton.innerHTML;

            copyMessageButton.innerHTML = "✓";
            copyMessageButton.title = "Copied";

            setTimeout(() => {
                copyMessageButton.innerHTML =
                    originalIcon;

                copyMessageButton.title =
                    role === "user"
                        ? "Copy question"
                        : "Copy answer";
            }, 1200);

        } catch (error) {
            showToast(
                "Unable to copy the message.",
                "error"
            );
        }
    }
);

    if (
        role === "assistant" &&
        sources.length > 0
    ) {
        const uniqueSources = [];
        const sourceKeys = new Set();

        sources.forEach((source) => {
            const key =
                `${source.filename}-${source.page_number}`;

            if (!sourceKeys.has(key)) {
                sourceKeys.add(key);
                uniqueSources.push(source);
            }
        });

        const sourceContainer =
            document.createElement("div");

        sourceContainer.className =
            "message-sources";

        sourceContainer.innerHTML =
    uniqueSources.map(
        (source) => `
            <details class="source-card">

                <summary class="source-card-summary">

                    <span class="source-card-title">
                        ${escapeHtml(
                            source.filename
                        )}
                        · Page
                        ${source.page_number ?? "-"}
                    </span>

                    <span class="source-card-score">
                        ${Number(
                            source.similarity || 0
                        ).toFixed(3)}
                        <span class="source-chevron">
                            ⌄
                        </span>
                    </span>

                </summary>

                <div class="source-card-content">
                    ${escapeHtml(
                        source.content ||
                        "Preview is unavailable for this older message."
                    )}
                    <button
                        class="source-preview-button"
                        type="button"
                        data-document-id="${source.document_id}"
                        data-page-number="${source.page_number || ""}"
                    >
                        View document page
                    </button>
                </div>

            </details>
        `
    ).join("");

        messageElement.appendChild(
            sourceContainer
        );
    }

    chatMessages.appendChild(messageElement);

if (role === "user") {
    scrollChatToBottom();
} else {
    window.requestAnimationFrame(() => {
        messageElement.scrollIntoView({
            behavior: "smooth",
            block: "start",
        });
    });
}

return messageElement;
}


function addTypingIndicator() {
    const messageElement =
        document.createElement("article");

    messageElement.id = "typing-message";
    messageElement.className =
        "message message-assistant";

    messageElement.innerHTML = `
        <div class="message-label">
            Assistant
        </div>

        <div class="message-content typing-indicator">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;

    chatMessages.appendChild(messageElement);
    scrollChatToBottom();
}


function removeTypingIndicator() {
    document
        .getElementById("typing-message")
        ?.remove();
}


function scrollChatToBottom() {
    window.requestAnimationFrame(() => {
        chatMessages.scrollTop =
            chatMessages.scrollHeight;
    });
}


// ==================================================
// Send messages
// ==================================================
function setGeneratingState(isGenerating) {
    state.isSending = isGenerating;

    sendButton.classList.toggle(
        "hidden",
        isGenerating
    );

    stopButton.classList.toggle(
        "hidden",
        !isGenerating
    );

    chatInput.disabled = isGenerating;
}


function createFollowUpQuestions(
    question,
    sources
) {
    if (!sources || sources.length === 0) {
        return [
            "What topics are covered in the selected documents?",
            "Can you summarize the selected documents?",
        ];
    }

    return [
        "Can you explain that in simpler terms?",
        "What are the most important points about this?",
        "Can you give an example from the selected documents?",
    ];
}


function addAssistantTools(
    messageElement,
    question,
    sources = []
) {
    document
        .querySelectorAll(".assistant-tools")
        .forEach((element) => {
            element.remove();
        });

    const toolsContainer =
        document.createElement("div");

    toolsContainer.className =
        "assistant-tools";

    const regenerateButton =
        document.createElement("button");

    regenerateButton.type = "button";
    regenerateButton.className =
        "regenerate-answer-button";

    regenerateButton.textContent =
        "↻ Regenerate answer";

    regenerateButton.addEventListener(
        "click",
        regenerateLastAnswer
    );

    const followUpHeading =
        document.createElement("div");

    followUpHeading.className =
        "follow-up-heading";

    followUpHeading.textContent =
        "Suggested follow-ups";

    const followUpList =
        document.createElement("div");

    followUpList.className =
        "follow-up-list";

    createFollowUpQuestions(
        question,
        sources
    ).forEach((suggestion) => {
        const suggestionButton =
            document.createElement("button");

        suggestionButton.type = "button";
        suggestionButton.className =
            "follow-up-button";

        suggestionButton.textContent =
            suggestion;

        suggestionButton.addEventListener(
            "click",
            () => {
                sendMessage(suggestion);
            }
        );

        followUpList.appendChild(
            suggestionButton
        );
    });

    toolsContainer.appendChild(
        regenerateButton
    );

    toolsContainer.appendChild(
        followUpHeading
    );

    toolsContainer.appendChild(
        followUpList
    );

    messageElement.appendChild(
        toolsContainer
    );
}
async function sendMessage(question) {
    if (state.isSending) {
        return;
    }

    const cleanQuestion = question.trim();

    if (!cleanQuestion) {
        return;
    }

    const readyDocuments =
        state.documents.filter(
            (document) =>
                document.status === "ready"
        );

    if (readyDocuments.length === 0) {
        showToast(
            "Upload at least one document first.",
            true
        );

        showView("upload");
        return;
    }

    const controller =
        new AbortController();

    state.activeRequestController =
        controller;

    setGeneratingState(true);

    try {
        if (!state.currentChatId) {
            await createNewChat();
        }

        appendMessage(
            "user",
            cleanQuestion
        );

        chatInput.value = "";
        resizeChatInput();
        addTypingIndicator();

        const data = await apiRequest(
            `/api/chats/${state.currentChatId}/messages`,
            {
                method: "POST",
                headers: {
                    "Content-Type":
                        "application/json",
                },
                body: JSON.stringify({
                    question: cleanQuestion,
                    document_ids:
                        state.selectedDocumentIds,
                }),
                signal: controller.signal,
            }
        );

        removeTypingIndicator();

        const assistantElement =
            appendMessage(
                "assistant",
                data.assistant_message.content,
                data.assistant_message.sources
            );

        addAssistantTools(
            assistantElement,
            cleanQuestion,
            data.assistant_message.sources
        );

        await loadChats();

        const currentChat =
            state.chats.find(
                (chat) =>
                    chat.id ===
                    state.currentChatId
            );

        if (currentChat) {
            currentChatTitle.textContent =
                currentChat.title;
        }
    } catch (error) {
        removeTypingIndicator();

        if (error.name === "AbortError") {
            showToast(
                "Generation stopped."
            );
        } else {
            showToast(
                error.message,
                true
            );
        }
    } finally {
        state.activeRequestController = null;
        setGeneratingState(false);
        chatInput.focus();
    }
}


chatForm.addEventListener(
    "submit",
    (event) => {
        event.preventDefault();
        sendMessage(chatInput.value);
    }
);


// Enter sends; Shift + Enter creates a new line
chatInput.addEventListener(
    "keydown",
    (event) => {
        if (
            event.key === "Enter" &&
            !event.shiftKey
        ) {
            event.preventDefault();

            if (!state.isSending) {
                chatForm.requestSubmit();
            }
        }
    }
);


chatInput.addEventListener(
    "input",
    resizeChatInput
);


function resizeChatInput() {
    chatInput.style.height = "auto";

    chatInput.style.height =
        `${Math.min(
            chatInput.scrollHeight,
            150
        )}px`;
}


document
    .querySelectorAll(".suggestion-button")
    .forEach((button) => {
        button.addEventListener(
            "click",
            () => {
                chatInput.value =
                    button.textContent.trim();

                sendMessage(chatInput.value);
            }
        );
    });
stopButton.addEventListener(
    "click",
    () => {
        if (state.activeRequestController) {
            state.activeRequestController.abort();
        }
    }
);


async function regenerateLastAnswer() {
    if (
        state.isSending ||
        !state.currentChatId
    ) {
        return;
    }

    const controller =
        new AbortController();

    state.activeRequestController =
        controller;

    setGeneratingState(true);
    addTypingIndicator();

    try {
        await apiRequest(
            `/api/chats/${state.currentChatId}/regenerate`,
            {
                method: "POST",
                headers: {
                    "Content-Type":
                        "application/json",
                },
                body: JSON.stringify({
                    document_ids:
                        state.selectedDocumentIds,
                }),
                signal: controller.signal,
            }
        );

        removeTypingIndicator();

        await openChat(
            state.currentChatId,
            true
        );

        showToast(
            "Answer regenerated."
        );
    } catch (error) {
        removeTypingIndicator();

        if (error.name === "AbortError") {
            showToast(
                "Regeneration stopped."
            );
        } else {
            showToast(
                error.message,
                true
            );
        }
    } finally {
        state.activeRequestController = null;
        setGeneratingState(false);
        chatInput.focus();
    }
}

// ==================================================
// Delete confirmation
// ==================================================

function openDeleteConfirmation(item) {
    state.pendingDelete = item;

    confirmationMessage.textContent =
        item.type === "document"
            ? `Delete "${item.name}" and all its chunks and embeddings?`
            : `Delete the chat "${item.name}" and all its messages?`;

    confirmationModal.classList.remove(
        "hidden"
    );
}


function closeDeleteConfirmation() {
    state.pendingDelete = null;

    confirmationModal.classList.add(
        "hidden"
    );
}


cancelConfirmationButton.addEventListener(
    "click",
    closeDeleteConfirmation
);


confirmDeleteButton.addEventListener(
    "click",
    async () => {
        const item = state.pendingDelete;

        if (!item) {
            return;
        }

        confirmDeleteButton.disabled = true;

        try {
            if (item.type === "document") {
                await apiRequest(
                    `/api/documents/${item.id}`,
                    {
                        method: "DELETE",
                    }
                );

                state.selectedDocumentIds =
                    state.selectedDocumentIds
                        .filter(
                            (id) => id !== item.id
                        );

                await loadDocuments();

                showToast(
                    "Document and embeddings deleted."
                );

            } else {
                await apiRequest(
                    `/api/chats/${item.id}`,
                    {
                        method: "DELETE",
                    }
                );

                if (
                    state.currentChatId ===
                    item.id
                ) {
                    state.currentChatId = null;
                    currentChatTitle.textContent =
                        "New chat";
                    clearChatMessages();
                }

                await loadChats();

                showToast("Chat deleted.");
            }

            closeDeleteConfirmation();

        } catch (error) {
            showToast(error.message, true);

        } finally {
            confirmDeleteButton.disabled = false;
        }
    }
);


// Close modals when clicking their dark background

documentSelectionModal.addEventListener(
    "click",
    (event) => {
        if (
            event.target ===
            documentSelectionModal
        ) {
            closeDocumentSelectionModal();
        }
    }
);


confirmationModal.addEventListener(
    "click",
    (event) => {
        if (
            event.target ===
            confirmationModal
        ) {
            closeDeleteConfirmation();
        }
    }
);

async function loadCurrentUser() {
    try {
        const user = await apiRequest(
            "/api/auth/me"
        );

        sidebarUsername.textContent =
            user.username || "User";

    } catch (error) {
        window.location.replace("/login");
        throw error;
    }
}

// ==================================================
// Retrieval analytics
// ==================================================

function formatRetrievalScore(value) {
    if (
        value === null ||
        value === undefined
    ) {
        return "-";
    }

    return Number(value).toFixed(3);
}


async function loadRetrievalAnalytics() {
    try {
        showLoading(
            "Loading retrieval analytics..."
        );

        const data = await apiRequest(
            "/api/retrieval-analytics"
        );

        const statistics =
            data.statistics || {};

        state.retrievalRuns =
            data.runs || [];

        analyticsTotalRuns.textContent =
            statistics.total_runs || 0;

        analyticsTotalChunks.textContent =
            statistics.total_context_chunks || 0;

        analyticsAverageChunks.textContent =
            statistics.average_context_chunks || 0;

        analyticsAverageSimilarity.textContent =
            formatRetrievalScore(
                statistics.average_similarity
            );

        analyticsClaudeCalls.textContent =
            statistics.claude_call_count || 0;

        renderRetrievalRuns();

    } catch (error) {
        showToast(error.message, true);

    } finally {
        hideLoading();
    }
}


function renderRetrievalRuns() {
    const searchText = (
        analyticsSearchInput.value || ""
    ).trim().toLowerCase();

    const filteredRuns =
        state.retrievalRuns.filter((run) => {
            const searchableText = [
                run.id,
                run.chat_title,
                run.question,
                run.request_type,
            ].join(" ").toLowerCase();

            return searchableText.includes(
                searchText
            );
        });

    if (filteredRuns.length === 0) {
        analyticsRunsTableBody.innerHTML = `
            <tr>
                <td
                    colspan="9"
                    class="table-empty-message"
                >
                    No retrieval runs found
                </td>
            </tr>
        `;

        return;
    }

    analyticsRunsTableBody.innerHTML =
        filteredRuns.map((run) => `
            <tr>
                <td class="analytics-run-id">
                    #${run.id}
                </td>

                <td
                    class="analytics-chat-title"
                    title="${escapeHtml(
                        run.chat_title
                    )}"
                >
                    ${escapeHtml(
                        run.chat_title
                    )}
                </td>

                <td
                    class="analytics-question"
                    title="${escapeHtml(
                        run.question
                    )}"
                >
                    ${escapeHtml(
                        run.question
                    )}
                </td>

                <td>
                    <span class="candidate-counts">
                        V ${run.vector_candidate_count ?? 0}
                        · K ${run.keyword_candidate_count ?? 0}
                        · C ${run.combined_candidate_count ?? 0}
                    </span>
                </td>

                <td>
                    ${run.context_count ?? 0}
                </td>

                <td>
                    ${formatRetrievalScore(
                        run.highest_similarity
                    )}
                </td>

                <td>
                    <span class="analytics-call-badge ${
                        run.claude_called
                            ? "called"
                            : "skipped"
                    }">
                        ${
                            run.claude_called
                                ? "Called"
                                : "Skipped"
                        }
                    </span>
                </td>

                <td>
                    ${formatDate(run.created_at)}
                </td>

                <td>
                    <button
                        class="view-retrieval-run-button"
                        type="button"
                        data-run-id="${run.id}"
                    >
                        View
                    </button>
                </td>
            </tr>
        `).join("");
}


async function openRetrievalRunDetails(
    runId
) {
    try {
        showLoading(
            "Loading retrieved chunks..."
        );

        const data = await apiRequest(
            `/api/retrieval-analytics/${runId}`
        );

        const run = data.run;
        const chunks = data.chunks || [];

        retrievalDetailsTitle.textContent =
            `Run #${run.id} · ${run.chat_title}`;

        retrievalRunSummary.innerHTML = `
            <div class="retrieval-summary-item wide">
                <span>Question</span>
                <strong>
                    ${escapeHtml(run.question)}
                </strong>
            </div>

            <div class="retrieval-summary-item wide">
                <span>Retrieval query</span>
                <strong>
                    ${escapeHtml(
                        run.retrieval_query ||
                        run.question
                    )}
                </strong>
            </div>

            <div class="retrieval-summary-item">
                <span>Vector candidates</span>
                <strong>
                    ${run.vector_candidate_count ?? 0}
                </strong>
            </div>

            <div class="retrieval-summary-item">
                <span>Keyword candidates</span>
                <strong>
                    ${run.keyword_candidate_count ?? 0}
                </strong>
            </div>

            <div class="retrieval-summary-item">
                <span>Combined candidates</span>
                <strong>
                    ${run.combined_candidate_count ?? 0}
                </strong>
            </div>

            <div class="retrieval-summary-item">
                <span>Final context chunks</span>
                <strong>
                    ${run.context_count ?? 0}
                </strong>
            </div>

            <div class="retrieval-summary-item">
                <span>Highest similarity</span>
                <strong>
                    ${formatRetrievalScore(
                        run.highest_similarity
                    )}
                </strong>
            </div>

            <div class="retrieval-summary-item">
                <span>Minimum similarity</span>
                <strong>
                    ${formatRetrievalScore(
                        run.minimum_similarity
                    )}
                </strong>
            </div>
        `;

        if (chunks.length === 0) {
            retrievalChunksList.innerHTML = `
                <div class="analytics-empty-panel">
                    No context chunks were supplied
                    to Claude for this run.
                </div>
            `;
        } else {
            retrievalChunksList.innerHTML =
                chunks.map((chunk) => `
                    <article class="retrieval-chunk-card">
                        <header>
                            <div>
                                <span class="chunk-position">
                                    Context ${
                                        chunk.context_position
                                    }
                                </span>

                                <strong>
                                    ${escapeHtml(
                                        chunk.filename
                                    )}
                                </strong>
                            </div>

                            <span class="chunk-page">
                                Page ${chunk.page_number}
                            </span>
                        </header>

                        <div class="chunk-score-row">
                            <span>
                                Type:
                                ${escapeHtml(
                                    chunk.retrieval_type ||
                                    "context"
                                )}
                            </span>

                            <span>
                                Similarity:
                                ${formatRetrievalScore(
                                    chunk.similarity_score
                                )}
                            </span>

                            <span>
                                Keyword:
                                ${formatRetrievalScore(
                                    chunk.keyword_score
                                )}
                            </span>

                            <span>
                                Reranker:
                                ${formatRetrievalScore(
                                    chunk.reranker_score
                                )}
                            </span>
                        </div>

                        <p>
                            ${escapeHtml(chunk.content)}
                        </p>
                    </article>
                `).join("");
        }

        retrievalDetailsPanel.classList.remove(
            "hidden"
        );

        requestAnimationFrame(() => {
            retrievalDetailsPanel.scrollIntoView({
                behavior: "smooth",
                block: "start",
            });
        });

    } catch (error) {
        showToast(error.message, true);

    } finally {
        hideLoading();
    }
}


analyticsSearchInput.addEventListener(
    "input",
    renderRetrievalRuns
);


refreshAnalyticsButton.addEventListener(
    "click",
    loadRetrievalAnalytics
);


analyticsRunsTableBody.addEventListener(
    "click",
    (event) => {
        const viewButton =
            event.target.closest(
                ".view-retrieval-run-button"
            );

        if (!viewButton) {
            return;
        }

        const runId = Number(
            viewButton.dataset.runId
        );

        if (!Number.isInteger(runId)) {
            showToast(
                "Invalid retrieval run.",
                true
            );
            return;
        }

        openRetrievalRunDetails(runId);
    }
);


closeRetrievalDetailsButton.addEventListener(
    "click",
    () => {
        retrievalDetailsPanel.classList.add(
            "hidden"
        );
    }
);


// ==================================================
// Initial application load
// ==================================================

async function initializeApplication() {
    await loadCurrentUser();

    await loadDocuments();

    const readyDocumentIds =
        state.documents
            .filter(
                (document) =>
                    document.status === "ready"
            )
            .map(
                (document) => document.id
            );

    state.selectedDocumentIds =
        readyDocumentIds;

    updateSelectedDocumentsSummary();

    await loadChats();

    if (state.chats.length > 0) {
        await openChat(state.chats[0].id);
    } else {
        clearChatMessages();
    }
}

initializeApplication();

// ==================================================
// Rename chat
// ==================================================

let chatBeingRenamedId = null;


function toggleChatMenu(event, chatId) {
    event.stopPropagation();

    const selectedMenu =
        document.getElementById(
            `chat-menu-${chatId}`
        );

    if (!selectedMenu) {
        return;
    }

    document
        .querySelectorAll(".chat-options-menu")
        .forEach((menu) => {
            if (menu !== selectedMenu) {
                menu.classList.add("hidden");
            }
        });

    selectedMenu.classList.toggle("hidden");
}


function openRenameChat(event, chatId) {
    event.stopPropagation();

    const chat = state.chats.find(
        (item) => item.id === chatId
    );

    if (!chat) {
        showToast("Chat not found.", true);
        return;
    }

    chatBeingRenamedId = chatId;

    document
        .getElementById(`chat-menu-${chatId}`)
        ?.classList.add("hidden");

    const renameModal =
        document.getElementById(
            "rename-chat-modal"
        );

    const renameInput =
        document.getElementById(
            "rename-chat-input"
        );

    renameInput.value = chat.title;
    renameModal.classList.remove("hidden");

    window.setTimeout(() => {
        renameInput.focus();
        renameInput.select();
    }, 50);
}


function closeRenameChat() {
    const renameModal =
        document.getElementById(
            "rename-chat-modal"
        );

    const renameInput =
        document.getElementById(
            "rename-chat-input"
        );

    renameModal.classList.add("hidden");
    renameInput.value = "";
    chatBeingRenamedId = null;
}


async function saveRenamedChat() {
    const renameInput =
        document.getElementById(
            "rename-chat-input"
        );

    const saveRenameButton =
        document.getElementById(
            "save-rename-button"
        );

    const newTitle =
        renameInput.value.trim();

    if (!newTitle) {
        showToast(
            "Please enter a chat name.",
            true
        );

        renameInput.focus();
        return;
    }

    if (chatBeingRenamedId === null) {
        return;
    }

    const renamedChatId =
        chatBeingRenamedId;

    saveRenameButton.disabled = true;
    saveRenameButton.textContent =
        "Saving...";

    try {
        await apiRequest(
            `/api/chats/${renamedChatId}`,
            {
                method: "PATCH",
                headers: {
                    "Content-Type":
                        "application/json",
                },
                body: JSON.stringify({
                    title: newTitle,
                }),
            }
        );

        closeRenameChat();
        await loadChats();

        if (
            state.currentChatId ===
            renamedChatId
        ) {
            currentChatTitle.textContent =
                newTitle;
        }

        showToast(
            "Chat renamed successfully."
        );

    } catch (error) {
        showToast(error.message, true);

    } finally {
        saveRenameButton.disabled = false;
        saveRenameButton.textContent =
            "Save";
    }
}


document
    .getElementById("save-rename-button")
    .addEventListener(
        "click",
        saveRenamedChat
    );


document
    .getElementById("cancel-rename-button")
    .addEventListener(
        "click",
        closeRenameChat
    );


document
    .getElementById("rename-chat-input")
    .addEventListener(
        "keydown",
        (event) => {
            if (event.key === "Enter") {
                event.preventDefault();
                saveRenamedChat();
            }

            if (event.key === "Escape") {
                closeRenameChat();
            }
        }
    );


document
    .getElementById("rename-chat-modal")
    .addEventListener(
        "click",
        (event) => {
            if (
                event.target.id ===
                "rename-chat-modal"
            ) {
                closeRenameChat();
            }
        }
    );


document.addEventListener(
    "click",
    () => {
        document
            .querySelectorAll(
                ".chat-options-menu"
            )
            .forEach((menu) => {
                menu.classList.add(
                    "hidden"
                );
            });
    }
);
