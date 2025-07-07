document.addEventListener('DOMContentLoaded', function () {
    const debugConsole = document.getElementById('debug-console');

    function logToPage(message, type = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = document.createElement('div');
        let color = '#00ff00';
        if (type === 'error') color = '#ff4444';
        else if (type === 'warn') color = '#ffbb33';
        logEntry.style.color = color;
        logEntry.textContent = `[${timestamp}] ${message}`;
        debugConsole.insertBefore(logEntry, debugConsole.firstChild);
        if (type === 'error') console.error(message);
        else console.log(message);
    }

    logToPage("DOM content loaded. Standalone mode initialized.");

    const textInput = document.getElementById('text-input');
    const pasteBtn = document.getElementById('paste-btn');
    const clearBtn = document.getElementById('clear-btn');
    const downloadBtn = document.getElementById('download-btn');
    const undoBtn = document.getElementById('undo-btn');
    const redoBtn = document.getElementById('redo-btn');

    let history = [textInput.value];
    let historyIndex = 0;

    function updateAllButtonsState() {
        const hasText = textInput.value.trim().length > 0;
        downloadBtn.disabled = !hasText;
        clearBtn.disabled = !hasText;
        undoBtn.disabled = historyIndex <= 0;
        redoBtn.disabled = historyIndex >= history.length - 1;
    }

    function saveState() {
        const currentValue = textInput.value;
        if (history[historyIndex] !== currentValue) {
            if (historyIndex < history.length - 1) {
                history = history.slice(0, historyIndex + 1);
            }
            history.push(currentValue);
            historyIndex = history.length - 1;
            updateAllButtonsState();
        }
    }

    function downloadTxtFile() {
        logToPage("--- Download process started ---");
        const textValue = textInput.value;

        if (textValue.length === 0) {
            logToPage("Validation failed: Text is empty.", 'warn');
            alert('The text field is empty!');
            return;
        }

        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const filename = `document_${year}-${month}-${day}_${hours}-${minutes}.txt`;

        logToPage(`Preparing file "${filename}" for download.`);

        const blob = new Blob([textValue], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;

        document.body.appendChild(link);
        link.click();

        document.body.removeChild(link);
        URL.revokeObjectURL(url);

        logToPage(`Download of "${filename}" initiated successfully.`, 'info');
    }

    textInput.addEventListener('input', saveState);

    pasteBtn.addEventListener('click', () => {
        navigator.clipboard.readText()
            .then(text => {
                textInput.value = text;
                saveState();
                logToPage("Text pasted from clipboard.");
            })
            .catch(err => {
                logToPage(`Failed to read clipboard: ${err.message}`, 'error');
                alert("Could not read from clipboard. Please use your device's paste function (e.g., Ctrl+V).");
            });
    });

    clearBtn.addEventListener('click', () => {
        textInput.value = '';
        saveState();
        logToPage("Text cleared.");
    });

    downloadBtn.addEventListener('click', downloadTxtFile);

    undoBtn.addEventListener('click', () => {
        if (historyIndex > 0) {
            historyIndex--;
            textInput.value = history[historyIndex];
            updateAllButtonsState();
        }
    });

    redoBtn.addEventListener('click', () => {
        if (historyIndex < history.length - 1) {
            historyIndex++;
            textInput.value = history[historyIndex];
            updateAllButtonsState();
        }
    });

    updateAllButtonsState();
});