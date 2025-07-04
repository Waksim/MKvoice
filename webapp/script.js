document.addEventListener('DOMContentLoaded', function () {
    const tg = window.Telegram.WebApp;
    const textInput = document.getElementById('text-input');
    const pasteBtn = document.getElementById('paste-btn');
    const sendBtn = document.getElementById('send-btn');

    // Inform the Telegram client that the app is ready
    tg.ready();

    // Configure the main button
    tg.MainButton.setText('Send Text');
    tg.MainButton.disable();

    // Event handler for the "Paste from Clipboard" button
    pasteBtn.addEventListener('click', () => {
        navigator.clipboard.readText()
            .then(text => {
                textInput.value = text;
                if (text.trim().length > 0) {
                    tg.MainButton.enable();
                } else {
                    tg.MainButton.disable();
                }
            })
            .catch(err => {
                console.error('Failed to read clipboard contents: ', err);
                tg.showAlert('Could not read from clipboard. Please paste manually.');
            });
    });

    // Event handler for the "Send to Bot" button
    sendBtn.addEventListener('click', () => {
        const textValue = textInput.value.trim();
        if (textValue.length === 0) {
            tg.showAlert('Text cannot be empty!');
            return;
        }

        // Send data to the bot
        tg.sendData(JSON.stringify({ text: textValue }));
        // Optionally, you can close the web app after sending
        // tg.close();
    });

    // Enable/disable the main button based on text input
    textInput.addEventListener('input', () => {
        if (textInput.value.trim().length > 0) {
            tg.MainButton.enable();
        } else {
            tg.MainButton.disable();
        }
    });

    // Also handle sending via the main Telegram button
    tg.MainButton.onClick(() => {
        const textValue = textInput.value.trim();
        if (textValue.length > 0) {
            tg.sendData(JSON.stringify({ text: textValue }));
        }
    });
});