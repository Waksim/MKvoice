document.addEventListener('DOMContentLoaded', function () {
    const tg = window.Telegram.WebApp;

    // Получаем все элементы интерфейса
    const textInput = document.getElementById('text-input');
    const pasteBtn = document.getElementById('paste-btn');
    const clearBtn = document.getElementById('clear-btn');
    const sendBtn = document.getElementById('send-btn'); // Эта кнопка теперь будет дублировать MainButton
    const undoBtn = document.getElementById('undo-btn');
    const redoBtn = document.getElementById('redo-btn');

    // Настройка истории для Undo/Redo
    let history = [textInput.value];
    let historyIndex = 0;
    let debounceTimeout;

    // --- Функции для управления состоянием ---

    // Обновляет состояние всех кнопок (активна/неактивна)
    function updateButtonsState() {
        undoBtn.disabled = historyIndex <= 0;
        redoBtn.disabled = historyIndex >= history.length - 1;

        const hasText = textInput.value.trim().length > 0;
        sendBtn.disabled = !hasText;

        // Управляем состоянием главной кнопки Telegram
        if (hasText) {
            tg.MainButton.enable(); // Активируем кнопку, если есть текст
        } else {
            tg.MainButton.disable(); // Деактивируем, если текста нет
        }
    }

    // Сохраняет текущее состояние текста в историю
    function saveState() {
        if (historyIndex < history.length - 1) {
            history = history.slice(0, historyIndex + 1);
        }
        if (history[history.length - 1] !== textInput.value) {
            history.push(textInput.value);
            historyIndex = history.length - 1;
        }
        updateButtonsState();
    }

    // --- Инициализация ---

    tg.ready();

    // Конфигурируем и ПОКАЗЫВАЕМ главную кнопку
    tg.MainButton.setText('Send Text');
    tg.MainButton.show(); // <--- КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: показываем кнопку

    updateButtonsState(); // Устанавливаем начальное состояние кнопок

    // --- Обработчики событий ---

    textInput.addEventListener('input', () => {
        clearTimeout(debounceTimeout);
        debounceTimeout = setTimeout(saveState, 500);
        updateButtonsState();
    });

    pasteBtn.addEventListener('click', () => {
        navigator.clipboard.readText()
            .then(text => {
                textInput.value = text;
                saveState();
            })
            .catch(err => {
                console.error('Failed to read clipboard contents: ', err);
                tg.showAlert('Could not read from clipboard. Please paste manually.');
            });
    });

    clearBtn.addEventListener('click', () => {
        textInput.value = '';
        saveState();
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
        // Отправляем данные через официальный API
        tg.sendData(JSON.stringify({ text: textValue }));

        // Закрываем Web App после успешной отправки для лучшего UX
        tg.close();
    }

    // Привязываем функцию отправки и к нашей кнопке, и к главной кнопке Telegram
    sendBtn.addEventListener('click', sendData);
    tg.MainButton.onClick(sendData);
});