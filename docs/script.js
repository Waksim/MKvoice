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
    const downloadBtn = document.getElementById('download-btn'); // Кнопка переименована
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
            // Если мы откатились назад и начали печатать, удаляем "будущую" историю
            if (historyIndex < history.length - 1) {
                history = history.slice(0, historyIndex + 1);
            }
            // Сохраняем состояние, только если оно отличается от последнего
            if (history[history.length - 1] !== textInput.value) {
                history.push(textInput.value);
                historyIndex = history.length - 1;
            }
            updateAllButtonsState();
        }, 300); // Дебаунс для сохранения состояния
    }

    // ================== ИЗМЕНЕНИЕ: Новая функция для скачивания .txt файла ==================
    /**
     * Создает и инициирует скачивание текстового файла с содержимым из textarea.
     */
    function downloadTxtFile() {
        logToPage("--- Download process started ---");
        const textValue = textInput.value; // Берем текст как есть, trim() не нужен

        if (textValue.length === 0) {
            logToPage("Validation failed: Text is empty.", 'warn');
            alert('The text field is empty!');
            return;
        }

        // Запрашиваем имя файла у пользователя
        let filename = prompt("Enter a filename for your .txt file:", "document.txt");
        if (filename === null) { // Пользователь нажал "Отмена"
            logToPage("Download cancelled by user.", 'warn');
            return;
        }
        // Убедимся, что имя файла заканчивается на .txt
        if (!filename.toLowerCase().endsWith('.txt')) {
            filename += '.txt';
        }

        logToPage(`Preparing file "${filename}" for download.`);

        // 1. Создаем Blob (Binary Large Object) из текстовых данных
        const blob = new Blob([textValue], { type: 'text/plain;charset=utf-8' });

        // 2. Создаем временный URL для этого Blob
        const url = URL.createObjectURL(blob);

        // 3. Создаем временный элемент <a> для скачивания
        const link = document.createElement('a');
        link.href = url;
        link.download = filename; // Этот атрибут указывает браузеру скачать файл

        // 4. Добавляем элемент в DOM (необходимо для Firefox) и симулируем клик
        document.body.appendChild(link);
        link.click();

        // 5. Очистка: удаляем элемент и освобождаем URL
        document.body.removeChild(link);
        URL.revokeObjectURL(url);

        logToPage(`Download of "${filename}" initiated successfully.`, 'info');
    }
    // =====================================================================================================

    // --- Инициализация и настройка обработчиков ---

    textInput.addEventListener('input', saveState);

    pasteBtn.addEventListener('click', () => {
        // Используем современный Clipboard API
        navigator.clipboard.readText()
            .then(text => {
                textInput.value = text;
                saveState();
                updateAllButtonsState();
                logToPage("Text pasted from clipboard.");
            })
            .catch(err => {
                logToPage(`Failed to read clipboard: ${err.message}`, 'error');
                alert('Could not read from clipboard. Please paste manually.');
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

    // Привязываем НОВУЮ функцию скачивания к кнопке
    downloadBtn.addEventListener('click', downloadTxtFile);
    logToPage("Event listener for download button is set.");

    // Устанавливаем начальное состояние кнопок
    updateAllButtonsState();
});