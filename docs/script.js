document.addEventListener('DOMContentLoaded', function () {
    // 1. Проверяем, что объект Telegram Web App доступен
    if (!window.Telegram || !window.Telegram.WebApp) {
        console.error("Telegram Web App script is not loaded or initialized.");
        // Показываем ошибку пользователю, если скрипт не загрузился
        document.body.innerHTML = '<h1>Error</h1><p>Could not initialize Telegram Web App. Please open this page inside Telegram.</p>';
        return;
    }

    const tg = window.Telegram.WebApp;
    console.log("Telegram Web App object initialized:", tg);

    // 2. Вызываем необходимые методы Telegram Web App при старте
    tg.ready();   // Сообщаем Telegram, что приложение готово
    tg.expand();  // Растягиваем приложение на весь экран

    // 3. Получаем все элементы интерфейса
    const textInput = document.getElementById('text-input');
    const pasteBtn = document.getElementById('paste-btn');
    const clearBtn = document.getElementById('clear-btn');
    const sendBtn = document.getElementById('send-btn');
    const undoBtn = document.getElementById('undo-btn');
    const redoBtn = document.getElementById('redo-btn');

    // 4. Настройка истории для Undo/Redo
    let history = [textInput.value];
    let historyIndex = 0;
    let debounceTimeout;

    // --- Функции для управления состоянием ---

    /**
     * Обновляет состояние всех кнопок (активна/неактивна) в зависимости от наличия текста.
     */
    function updateAllButtonsState() {
        const hasText = textInput.value.trim().length > 0;

        // Включаем/выключаем главную кнопку Telegram
        // Кнопка уже видима, мы только управляем ее состоянием 'enabled'/'disabled'
        if (hasText) {
            tg.MainButton.enable();
        } else {
            tg.MainButton.disable();
        }

        // Включаем/выключаем кнопки на странице
        sendBtn.disabled = !hasText;
        clearBtn.disabled = !hasText;
        undoBtn.disabled = historyIndex <= 0;
        redoBtn.disabled = historyIndex >= history.length - 1;
    }

    /**
     * Сохраняет текущее состояние текста в историю для Undo/Redo.
     * Использует debounce для предотвращения слишком частых сохранений.
     */
    function saveState() {
        clearTimeout(debounceTimeout);
        debounceTimeout = setTimeout(() => {
            // Если мы откатывались назад и начали вводить новый текст,
            // удаляем "будущие" состояния
            if (historyIndex < history.length - 1) {
                history = history.slice(0, historyIndex + 1);
            }
            // Добавляем новое состояние, только если оно отличается от последнего
            if (history[history.length - 1] !== textInput.value) {
                history.push(textInput.value);
                historyIndex = history.length - 1;
                console.log(`State saved. History size: ${history.length}`);
            }
            updateAllButtonsState();
        }, 300); // Задержка в 300 мс
    }

    /**
     * Функция отправки данных боту.
     */
    function sendData() {
        const textValue = textInput.value.trim();
        if (textValue.length === 0) {
            tg.showAlert('Text cannot be empty!');
            return;
        }

        try {
            const dataToSend = JSON.stringify({ text: textValue });

            // ИЗМЕНЕНИЕ: Проверка на ограничение размера данных в Telegram Web App (4096 байт)
            // Используем Blob для точного подсчета байтов в UTF-8 строке.
            if (new Blob([dataToSend]).size > 4096) {
                tg.showAlert('The text is too long (max 4096 bytes). Please shorten it and try again.');
                return;
            }

            console.log("Sending data to bot:", dataToSend);

            // Официальный метод отправки данных
            tg.sendData(dataToSend);

            // ИЗМЕНЕНИЕ: Явно закрываем Web App после отправки данных.
            // Это гарантирует, что приложение закроется, и данные будут успешно переданы боту.
            tg.close();

        } catch (error) {
            console.error("Error during sending data:", error);
            tg.showAlert(`An error occurred: ${error.message}`);
        }
    }

    // --- Инициализация и настройка обработчиков ---

    // 5. Конфигурируем главную кнопку Telegram
    tg.MainButton.setText('Send Text');
    tg.MainButton.color = '#2ea6ff';
    tg.MainButton.textColor = '#ffffff';

    // --- ИЗМЕНЕНИЕ: Показываем кнопку один раз при инициализации.
    // Это гарантирует, что компонент будет отрисован и готов к работе.
    tg.MainButton.show();


    // 6. Устанавливаем обработчики событий для кнопок
    textInput.addEventListener('input', () => {
        // Убрали дублирующий вызов updateAllButtonsState(), так как он есть в saveState
        saveState();
    });

    pasteBtn.addEventListener('click', () => {
        navigator.clipboard.readText()
            .then(text => {
                textInput.value = text;
                saveState();
                updateAllButtonsState();
            })
            .catch(err => {
                console.error('Failed to read clipboard:', err);
                tg.showAlert('Could not read from clipboard. Please paste manually.');
            });
    });

    clearBtn.addEventListener('click', () => {
        textInput.value = '';
        saveState();
        updateAllButtonsState();
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
    tg.MainButton.onClick(sendData); // Надежный обработчик для главной кнопки

    // 8. Устанавливаем начальное состояние всех кнопок при загрузке страницы
    updateAllButtonsState();
});