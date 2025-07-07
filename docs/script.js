document.addEventListener('DOMContentLoaded', function () {
    const debugConsole = document.getElementById('debug-console');

    // ================== ФУНКЦИЯ ЛОГИРОВАНИЯ НА СТРАНИЦУ ==================
    function logToPage(message, type = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = document.createElement('div');
        let color = '#00ff00'; // Зеленый для info
        if (type === 'error') {
            color = '#ff4444'; // Красный для ошибок
        } else if (type === 'warn') {
            color = '#ffbb33'; // Желтый для предупреждений
        }
        logEntry.style.color = color;
        logEntry.textContent = `[${timestamp}] ${message}`;
        debugConsole.insertBefore(logEntry, debugConsole.firstChild);
        if (type === 'error') console.error(message);
        else if (type === 'warn') console.warn(message);
        else console.log(message);
    }
    // ===============================================================================

    logToPage("DOM content loaded. Initializing script...");

    const textInput = document.getElementById('text-input');
    const pasteBtn = document.getElementById('paste-btn');
    const clearBtn = document.getElementById('clear-btn');
    const downloadBtn = document.getElementById('download-btn');
    const undoBtn = document.getElementById('undo-btn');
    const redoBtn = document.getElementById('redo-btn');

    let history = [textInput.value];
    let historyIndex = 0;
    let debounceTimeout;

    function updateAllButtonsState() {
        const hasText = textInput.value.trim().length > 0;
        downloadBtn.disabled = !hasText;
        clearBtn.disabled = !hasText;
        undoBtn.disabled = historyIndex <= 0;
        redoBtn.disabled = historyIndex >= history.length - 1;
    }

    function saveState() {
        clearTimeout(debounceTimeout);
        debounceTimeout = setTimeout(() => {
            if (historyIndex < history.length - 1) {
                history = history.slice(0, historyIndex + 1);
            }
            if (history[history.length - 1] !== textInput.value) {
                history.push(textInput.value);
                historyIndex = history.length - 1;
            }
            updateAllButtonsState();
        }, 300);
    }

    // ================== ИЗМЕНЕНИЕ: Убрано диалоговое окно ==================
    /**
     * Создает и инициирует скачивание текстового файла с содержимым из textarea.
     * Имя файла генерируется автоматически.
     */
    function downloadTxtFile() {
        logToPage("--- Download process started ---");
        const textValue = textInput.value;

        if (textValue.length === 0) {
            logToPage("Validation failed: Text is empty.", 'warn');
            alert('The text field is empty!');
            return;
        }

        // --- НОВАЯ ЛОГИКА ГЕНЕРАЦИИ ИМЕНИ ФАЙЛА ---
        // Создаем объект даты
        const now = new Date();
        // Форматируем дату и время в удобную строку (ГГГГ-ММ-ДД_ЧЧ-ММ-СС)
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0'); // Месяцы от 0 до 11
        const day = String(now.getDate()).padStart(2, '0');
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const seconds = String(now.getSeconds()).padStart(2, '0');

        // Собираем имя файла, например "document_2025-07-07_10-30-15.txt"
        const filename = `document_${year}-${month}-${day}_${hours}-${minutes}-${seconds}.txt`;
        // --- КОНЕЦ НОВОЙ ЛОГИКИ ---

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
    // =====================================================================================================

    // --- Инициализация и настройка обработчиков ---

    textInput.addEventListener('input', saveState);

    pasteBtn.addEventListener('click', () => {
        navigator.clipboard.readText()
            .then(text => {
                textInput.value = text;
                saveState();
                updateAllButtonsState();
                logToPage("Text pasted from clipboard.");
            })
            .catch(err => {
                logToPage(`Failed to read clipboard: ${err.message}`, 'error');
                textInput.focus();
                alert("Could not read clipboard. Please use your device's paste function (Ctrl+V or long-press).");
            });
    });

    clearBtn.addEventListener('click', () => {
        textInput.value = '';
        saveState();
        updateAllButtonsState();
        logToPage("Text cleared.");
    });

    undoBtn.addEventListener('click', () => {
        if (historyIndex > 0) {
            historyIndex--;
            textInput.value = history[historyIndex];
            updateAllButtonsState();
            logToPage("Action: Undo.");
        }
    });

    redoBtn.addEventListener('click', () => {
        if (historyIndex < history.length - 1) {
            historyIndex++;
            textInput.value = history[historyIndex];
            updateAllButtonsState();
            logToPage("Action: Redo.");
        }
    });

    downloadBtn.addEventListener('click', downloadTxtFile);
    logToPage("Event listener for download button is set.");

    updateAllButtonsState();
});