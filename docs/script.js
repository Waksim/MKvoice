// docs/script.js (Минимальная тестовая версия)
document.addEventListener('DOMContentLoaded', function () {
    const tg = window.Telegram.WebApp;

    // Сразу же инициализируем приложение
    tg.ready();

    // Проверяем, доступен ли объект tg
    if (!tg || !tg.MainButton) {
        alert("Telegram Web App API не доступен!");
        return;
    }

    // Настраиваем главную кнопку
    tg.MainButton.setText("SEND TEST DATA");
    tg.MainButton.enable();
    tg.MainButton.show();

    // Вешаем обработчик на главную кнопку
    tg.MainButton.onClick(function() {
        try {
            const testData = {
                text: "Это тестовое сообщение из Web App!",
                timestamp: new Date().toISOString()
            };
            tg.sendData(JSON.stringify(testData));

            // Закрываем приложение после отправки
            // tg.close();
        } catch (e) {
            // Если что-то пошло не так, покажем ошибку
            alert("Ошибка при отправке: " + e.toString());
        }
    });
});