document.addEventListener('DOMContentLoaded', function () {
    const debugConsole = document.getElementById('debug-console');

    // ================== ИЗМЕНЕНИЕ: ФУНКЦИЯ ЛОГИРОВАНИЯ НА СТРАНИЦУ ==================
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

        // Добавляем новые логи сверху
        debugConsole.insertBefore(logEntry, debugConsole.firstChild);

        // Также выводим в настоящую консоль для отладки в браузере
        if (type === 'error') console.error(message);
        else if (type === 'warn') console.warn(message);
        else console.log(message);
    }
    // ===============================================================================

    logToPage("DOM content loaded. Initializing script...");

    // 1. Проверяем, что объект Telegram Web App доступен
    if (!window.Telegram || !window.Telegram.WebApp) {
        logToPage("Fatal: Telegram Web App script is not loaded or initialized.", 'error');
        document.body.innerHTML = '<h1>Error</h1><p>Could not initialize Telegram Web App. Please open this page inside Telegram.</p>';
        return;
    }

    const tg = window.Telegram.WebApp;
    logToPage("Telegram Web App object initialized successfully.");
    logToPage(`Theme params: ${JSON.stringify(tg.themeParams)}`, 'warn');

    // 2. Вызываем необходимые методы Telegram Web App при старте
    tg.ready();
    logToPage("tg.ready() called.");
    tg.expand();
    logToPage("tg.expand() called.");

    // 3. Получаем все элементы интерфейса
    const textInput = document.getElementById('text-input');
    const pasteBtn = document.getElementById('paste-btn');
    const clearBtn = document.getElementById('clear-btn');
    const sendBtn = document.getElementById('send-btn');
    const undoBtn = document.getElementById('undo-btn');
    const redoBtn = document.getElementById('redo-btn');

    // 4. Настройка истории для Undo/Redo (без изменений)
    let history = [textInput.value];
    let historyIndex = 0;
    let debounceTimeout;

    // --- Функции для управления состоянием (без изменений логики, но с добавлением логов) ---
    function updateAllButtonsState() {
        const hasText = textInput.value.trim().length > 0;
        if (hasText) {
            tg.MainButton.enable();
        } else {
            tg.MainButton.disable();
        }
        sendBtn.disabled = !hasText;
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

    // ================== ИЗМЕНЕНИЕ: Полностью переработанная функция sendData для отладки ==================
    /**
     * Функция отправки данных боту с подробным логированием каждого шага.
     */
    function sendData() {
        logToPage("--- Send process started ---");
        const textValue = textInput.value.trim();

        if (textValue.length === 0) {
            logToPage("Validation failed: Text is empty.", 'warn');
            tg.showAlert('Text cannot be empty!');
            return;
        }
        logToPage(`Text for sending: "${textValue.substring(0, 50)}..."`);

        try {
            const dataToSend = JSON.stringify({ text: textValue });
            logToPage(`Data stringified. Length: ${dataToSend.length} bytes.`);

            const dataSize = new Blob([dataToSend]).size;
            logToPage(`Payload size calculated: ${dataSize} bytes.`);

            if (dataSize > 4096) {
                logToPage(`Validation failed: The text is too long (size: ${dataSize} bytes).`, 'error');
                tg.showAlert(`The text is too long (max 4096 bytes, current: ${dataSize}). Please shorten it.`);
                return;
            }

            logToPage("All validations passed. Calling tg.sendData()...");

            // Самый важный вызов
            tg.sendData(dataToSend);

            logToPage("tg.sendData() was called. Now calling tg.close(). If the app closes but data is not received, the problem is likely on the bot's side or in Telegram's infrastructure.");

            // Закрываем приложение, чтобы завершить процесс
            // tg.close();

        } catch (error) {
            logToPage(`An unexpected error occurred during the send process: ${error.message}`, 'error');
            tg.showAlert(`An error occurred: ${error.message}`);
        }
    }
    // =====================================================================================================

    // --- Инициализация и настройка обработчиков ---

    // 5. Конфигурируем главную кнопку Telegram
    tg.MainButton.setText('Send Text');
    tg.MainButton.color = '#2ea6ff';
    tg.MainButton.textColor = '#ffffff';
    tg.MainButton.show();
    logToPage("MainButton configured and shown.");

    // 6. Устанавливаем обработчики событий для кнопок
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
                logToPage(`Failed to read clipboard: ${err}`, 'error');
                tg.showAlert('Could not read from clipboard. Please paste manually.');
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
        }
    });

    redoBtn.addEventListener('click', () => {
        if (historyIndex < history.length - 1) {
            historyIndex++;
            textInput.value = history[historyIndex];
            updateAllButtonsState();
        }
    });

    // 7. Привязываем функцию отправки к кнопкам
    sendBtn.addEventListener('click', sendData);
    tg.MainButton.onClick(sendData);
    logToPage("Event listeners for send buttons are set.");

    // 8. Устанавливаем начальное состояние всех кнопок при загрузке страницы
    updateAllButtonsState();
});