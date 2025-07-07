document.addEventListener('DOMContentLoaded', function () {
    const debugConsole = document.getElementById('debug-console');

    function logToPage(message, type = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = document.createElement('div');
        let color = '#00ff00';
        if (type === 'error') color = '#ff4444'; else if (type === 'warn') color = '#ffbb33';
        logEntry.style.color = color;
        logEntry.textContent = `[${timestamp}] ${message}`;
        debugConsole.insertBefore(logEntry, debugConsole.firstChild);
    }

    if (!window.Telegram || !window.Telegram.WebApp) {
        logToPage("Fatal: Not in Telegram. Limited functionality.", 'error');
        // Не блокируем, но некоторые функции не будут работать
    }

    const tg = window.Telegram.WebApp;
    tg.ready();
    tg.expand();
    logToPage("Telegram Web App initialized.");

    const textInput = document.getElementById('text-input');
    const pasteBtn = document.getElementById('paste-btn');
    const clearBtn = document.getElementById('clear-btn');
    const undoBtn = document.getElementById('undo-btn');
    const redoBtn = document.getElementById('redo-btn');

    let history = [textInput.value];
    let historyIndex = 0;

    function updateAllButtonsState() {
        const hasText = textInput.value.trim().length > 0;
        if (hasText) tg.MainButton.enable(); else tg.MainButton.disable();
        clearBtn.disabled = !hasText;
        undoBtn.disabled = historyIndex <= 0;
        redoBtn.disabled = historyIndex >= history.length - 1;
    }

    function saveState() {
        // ... (логика сохранения истории для Undo/Redo остается прежней)
        const currentValue = textInput.value;
        if (history[historyIndex] !== currentValue) {
            if (historyIndex < history.length - 1) history = history.slice(0, historyIndex + 1);
            history.push(currentValue);
            historyIndex = history.length - 1;
            updateAllButtonsState();
        }
    }

    textInput.addEventListener('input', saveState);

    pasteBtn.addEventListener('click', () => {
        logToPage("Pasting via Telegram API...");
        tg.readTextFromClipboard(text => {
            if (text === null) {
                logToPage("Clipboard empty or permission denied.", 'warn');
                tg.showAlert("Clipboard is empty or access was denied.");
            } else {
                textInput.value = text;
                logToPage("Text pasted.");
                saveState();
            }
        });
    });

    clearBtn.addEventListener('click', () => { textInput.value = ''; saveState(); });
    undoBtn.addEventListener('click', () => { if (historyIndex > 0) { historyIndex--; textInput.value = history[historyIndex]; updateAllButtonsState(); } });
    redoBtn.addEventListener('click', () => { if (historyIndex < history.length - 1) { historyIndex++; textInput.value = history[historyIndex]; updateAllButtonsState(); } });

    // --- LZW-компрессия для уменьшения размера текста ---
    const LZW = {
        compress: (uncompressed) => {
            let dict = {};
            let data = (uncompressed + "").split("");
            let out = [];
            let currChar;
            let phrase = data[0];
            let code = 256;
            for (let i = 1; i < data.length; i++) {
                currChar = data[i];
                if (dict[phrase + currChar] != null) {
                    phrase += currChar;
                } else {
                    out.push(phrase.length > 1 ? dict[phrase] : phrase.charCodeAt(0));
                    dict[phrase + currChar] = code;
                    code++;
                    phrase = currChar;
                }
            }
            out.push(phrase.length > 1 ? dict[phrase] : phrase.charCodeAt(0));
            for (let i = 0; i < out.length; i++) {
                out[i] = String.fromCharCode(out[i]);
            }
            return out.join("");
        }
    };

    // --- ОСНОВНАЯ ФУНКЦИЯ: ПОДГОТОВКА И ПЕРЕНАПРАВЛЕНИЕ ---
    function prepareAndRedirectForDownload() {
        const text = textInput.value;
        if (text.trim().length === 0) {
            tg.showAlert("Text is empty!");
            return;
        }

        logToPage("Compressing text...");
        const compressedText = LZW.compress(text);
        logToPage(`Compression ratio: ${text.length} -> ${compressedText.length} chars`);

        const data = encodeURIComponent(compressedText);

        // ВАЖНО: Замените URL на ваш!
        const baseUrl = "https://waksim.github.io/MKttsBOT/"; // <-- ВАШ ПУТЬ НА GITHUB PAGES
        const downloadUrl = `${baseUrl}downloader.html?data=${data}`;

        if (downloadUrl.length > 4096) { // Запас прочности
             logToPage("URL too long even after compression.", "error");
             tg.showAlert("The text is too long to be processed this way. Please shorten it.");
             return;
        }

        logToPage("Redirecting to browser for download...");
        tg.openLink(downloadUrl);
    }

    tg.MainButton.setText("Open Download Page");
    tg.MainButton.onClick(prepareAndRedirectForDownload);
    tg.MainButton.show();

    updateAllButtonsState();
});