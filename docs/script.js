document.addEventListener('DOMContentLoaded', function () {
    // Проверяем, доступен ли объект Telegram Web App
    if (!window.Telegram || !window.Telegram.WebApp) {
        console.error("Telegram Web App script is not loaded or initialized.");
        document.body.innerHTML = '<h1>Error</h1><p>Could not initialize Telegram Web App. Please open this page inside Telegram.</p>';
        return;
    }

    const tg = window.Telegram.WebApp;
    console.log("Telegram Web App object initialized:", tg);

    // Расширяем Web App на весь экран
    tg.expand();

    // Получаем все элементы интерфейса
    const textInput = document.getElementById('text-input');
    const pasteBtn = document.getElementById('paste-btn');
    const clearBtn = document.getElementById('clear-btn');
    const sendBtn = document.getElementById('send-btn');
    const undoBtn = document.getElementById('undo-btn');
    const redoBtn = document.getElementById('redo-btn');

    // Настройка истории для Undo/Redo
    let history = [textInput.value];
    let historyIndex = 0;
    let debounceTimeout;

    // --- Функции для управления состоянием ---

    function updateButtonsState() {
        const hasText = textInput.value.trim().length > 0;

        undoBtn.disabled = historyIndex <= 0;
        redoBtn.disabled = historyIndex >= history.length - 1;
        sendBtn.disabled = !hasText;
        clearBtn.disabled = !hasText;

        // Управляем состоянием главной кнопки Telegram
        if (hasText) {
            tg.MainButton.enable();
        } else {
            tg.MainButton.disable();
        }
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
            updateButtonsState();
        }, 500);
    }

    // --- Инициализация ---

    tg.ready();
    console.log("tg.ready() called.");

    // Конфигурируем и, что ВАЖНО, ПОКАЗЫВАЕМ главную кнопку
    tg.MainButton.setText('Send Text');
    tg.MainButton.color = '#2ea6ff';
    tg.MainButton.textColor = '#ffffff';
    tg.MainButton.show(); // <--- ИСПРАВЛЕНИЕ: Показываем кнопку сразу

    // Инициализируем состояние кнопок при загрузке
    updateButtonsState();

    // --- Обработчики событий ---

    textInput.addEventListener('input', () => {
        saveState();
        updateButtonsState();
    });

    pasteBtn.addEventListener('click', () => {
        navigator.clipboard.readText()
            .then(text => {
                textInput.value = text;
                saveState();
                updateButtonsState();
            })
            .catch(err => {
                console.error('Failed to read clipboard contents: ', err);
                tg.showAlert('Could not read from clipboard. Please paste manually.');
            });
    });

    clearBtn.addEventListener('click', () => {
        textInput.value = '';
        saveState();
        updateButtonsState();
    });

    undoBtn.addEventListener('click', () => {
        if (historyIndex > 0) {
            historyIndex--;
            textInput.value = history[historyIndex];
            updateButtonsState();
        }
    });

    redoBtn.addEventListener('click', () => {
        if (historyIndex < history.length - 1) {
            historyIndex++;
            textInput.value = history[historyIndex];
            updateButtonsState();
        }
    });

    // Функция отправки данных
    function sendData() {
        const textValue = textInput.value.trim();
        if (textValue.length === 0) {
            tg.showAlert('Text cannot be empty!');
            return;
        }

        try {
            const dataToSend = JSON.stringify({ text: textValue });
            console.log("Sending data to bot:", dataToSend);
            tg.sendData(dataToSend);

            // Раскомментируйте, когда убедитесь, что все работает
            // tg.close();
        } catch (error) {
            console.error("Error sending data:", error);
            tg.showAlert(`An error occurred while sending data: ${error.message}`);
        }
    }

    // Привязываем функцию отправки к обеим кнопкам
    sendBtn.addEventListener('click', sendData);
    tg.MainButton.onClick(sendData); // <--- ИСПРАВЛЕНИЕ: Возвращаем надежный .onClick()
});