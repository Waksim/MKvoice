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

    if (!window.Telegram || !window.Telegram.WebApp) {
        logToPage("Fatal: Telegram Web App script is not loaded or initialized.", 'error');
        document.body.innerHTML = '<h1>Error</h1><p>Could not initialize Telegram Web App. Please open this page inside Telegram.</p>';
        return;
    }

    const tg = window.Telegram.WebApp;
    logToPage("Telegram Web App object initialized successfully.");
    logToPage(`Theme params: ${JSON.stringify(tg.themeParams)}`, 'warn');
    logToPage(`User data: ${JSON.stringify(tg.initDataUnsafe.user)}`, 'warn');


    tg.ready();
    logToPage("tg.ready() called.");
    tg.expand();
    logToPage("tg.expand() called.");

    const textInput = document.getElementById('text-input');
    const pasteBtn = document.getElementById('paste-btn');
    const clearBtn = document.getElementById('clear-btn');
    const sendBtn = document.getElementById('send-btn');
    const undoBtn = document.getElementById('undo-btn');
    const redoBtn = document.getElementById('redo-btn');

    let history = [textInput.value];
    let historyIndex = 0;
    let debounceTimeout;

    function updateAllButtonsState() {
        const hasText = textInput.value.trim().length > 0;
        // Главная кнопка Telegram теперь тоже управляется этой логикой
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

    // ================== ИЗМЕНЕНИЕ: Новая функция отправки данных на бэкенд ==================
    /**
     * Асинхронная функция отправки данных на внешний бэкенд-сервер.
     */
    async function sendDataToBackend() {
        logToPage("--- Send process started ---");
        const textValue = textInput.value.trim();

        if (textValue.length === 0) {
            logToPage("Validation failed: Text is empty.", 'warn');
            tg.showAlert('Text cannot be empty!');
            return;
        }

        // Получаем ID пользователя из данных инициализации Web App
        const userId = tg.initDataUnsafe.user.id;
        if (!userId) {
            logToPage("Fatal: Could not get user ID from Telegram.", 'error');
            tg.showAlert('Could not identify you. Please restart the bot and try again.');
            return;
        }

        logToPage(`Text for sending: "${textValue.substring(0, 50)}..."`);
        logToPage(`User ID: ${userId}`);

        // Делаем кнопки неактивными на время отправки
        sendBtn.disabled = true;
        tg.MainButton.showProgress();

        try {
            const backendUrl = 'http://89.110.119.205:8000/process-text'; // ВАШ АДРЕС СЕРВЕРА
            logToPage(`Sending POST request to ${backendUrl}`);

            const response = await fetch(backendUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: userId,
                    text: textValue,
                }),
            });

            const responseData = await response.json();

            if (!response.ok) {
                logToPage(`Server returned an error: ${response.status} - ${responseData.detail || 'Unknown error'}`, 'error');
                tg.showAlert(`Server error: ${responseData.detail || 'An unknown error occurred.'}`);
            } else {
                logToPage("Data sent successfully to backend.", 'info');
                tg.showAlert("Your text has been sent for processing. Please check the bot chat for the result.");
                // Закрываем Web App после успешной отправки
                tg.close();
            }

        } catch (error) {
            logToPage(`An unexpected network error occurred: ${error.message}`, 'error');
            tg.showAlert(`A network error occurred: ${error.message}. Please check your connection or contact the administrator.`);
        } finally {
            // Возвращаем кнопки в активное состояние
            sendBtn.disabled = false;
            tg.MainButton.hideProgress();
            updateAllButtonsState(); // Обновляем состояние на случай, если пользователь не закрыл окно
        }
    }
    // =====================================================================================================

    // --- Инициализация и настройка обработчиков ---

    tg.MainButton.setText('Send Text');
    tg.MainButton.color = '#2ea6ff';
    tg.MainButton.textColor = '#ffffff';
    tg.MainButton.show();
    logToPage("MainButton configured and shown.");

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

    // Привязываем НОВУЮ функцию отправки к кнопкам
    sendBtn.addEventListener('click', sendDataToBackend);
    tg.MainButton.onClick(sendDataToBackend);
    logToPage("Event listeners for send buttons are set.");

    updateAllButtonsState();
});