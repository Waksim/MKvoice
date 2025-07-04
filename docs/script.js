document.addEventListener('DOMContentLoaded', function () {
    const tg = window.Telegram.WebApp;

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

    // Обновляет состояние всех кнопок (активна/неактивна)
    function updateButtonsState() {
        // Кнопка Undo активна, если мы не в самом начале истории
        undoBtn.disabled = historyIndex <= 0;
        // Кнопка Redo активна, если мы не в самом конце истории
        redoBtn.disabled = historyIndex >= history.length - 1;
        // Кнопка Send активна, если в поле есть текст
        const hasText = textInput.value.trim().length > 0;
        sendBtn.disabled = !hasText;
        if (hasText) {
            tg.MainButton.enable();
        } else {
            tg.MainButton.disable();
        }
    }

    // Сохраняет текущее состояние текста в историю
    function saveState() {
        // Если мы отменили действия и начали печатать, "будущие" шаги удаляются
        if (historyIndex < history.length - 1) {
            history = history.slice(0, historyIndex + 1);
        }
        // Не сохраняем состояние, если оно не изменилось
        if (history[history.length - 1] !== textInput.value) {
            history.push(textInput.value);
            historyIndex = history.length - 1;
        }
        updateButtonsState();
    }

    // --- Инициализация ---

    tg.ready();
    tg.MainButton.setText('Send Text');
    updateButtonsState(); // Устанавливаем начальное состояние кнопок

    // --- Обработчики событий ---

    // Ввод текста с задержкой для сохранения истории
    textInput.addEventListener('input', () => {
        clearTimeout(debounceTimeout);
        debounceTimeout = setTimeout(saveState, 500); // Сохраняем через 500 мс после паузы
        updateButtonsState(); // Обновляем кнопку Send немедленно
    });

    // Кнопка "Вставить"
    pasteBtn.addEventListener('click', () => {
        navigator.clipboard.readText()
            .then(text => {
                textInput.value = text;
                saveState(); // Сохраняем новое состояние после вставки
            })
            .catch(err => {
                console.error('Failed to read clipboard contents: ', err);
                tg.showAlert('Could not read from clipboard. Please paste manually.');
            });
    });

    // Кнопка "Очистить"
    clearBtn.addEventListener('click', () => {
        textInput.value = '';
        saveState(); // Сохраняем пустое состояние
    });

    // Кнопка "Отменить" (Undo)
    undoBtn.addEventListener('click', () => {
        if (historyIndex > 0) {
            historyIndex--;
            textInput.value = history[historyIndex];
            updateButtonsState();
        }
    });

    // Кнопка "Повторить" (Redo)
    redoBtn.addEventListener('click', () => {
        if (historyIndex < history.length - 1) {
            historyIndex++;
            textInput.value = history[historyIndex];
            updateButtonsState();
        }
    });

    // Кнопка "Отправить"
    function sendData() {
        const textValue = textInput.value.trim();
        if (textValue.length === 0) {
            tg.showAlert('Text cannot be empty!');
            return;
        }
        tg.sendData(JSON.stringify({ text: textValue }));
    }

    sendBtn.addEventListener('click', sendData);
    tg.MainButton.onClick(sendData);
});