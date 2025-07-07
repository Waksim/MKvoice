document.addEventListener('DOMContentLoaded', function () {
    // --- LZW-декомпрессия ---
    const LZW = {
        decompress: (s) => {
            let dict = {};
            let data = (s + "").split("");
            let currChar = data[0];
            let oldPhrase = currChar;
            let out = [currChar];
            let code = 256;
            let phrase;
            for (let i = 1; i < data.length; i++) {
                let currCode = data[i].charCodeAt(0);
                if (currCode < 256) {
                    phrase = data[i];
                } else {
                    phrase = dict[currCode] ? dict[currCode] : (oldPhrase + currChar);
                }
                out.push(phrase);
                currChar = phrase.charAt(0);
                dict[code] = oldPhrase + currChar;
                code++;
                oldPhrase = phrase;
            }
            return out.join("");
        }
    };

    try {
        const urlParams = new URLSearchParams(window.location.search);
        const compressedData = urlParams.get('data');

        if (!compressedData) {
            throw new Error("No data found in URL.");
        }

        const decodedData = decodeURIComponent(compressedData);
        const text = LZW.decompress(decodedData);

        // --- Логика скачивания (работает в обычном браузере) ---
        const now = new Date();
        const timestamp = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}_${String(now.getHours()).padStart(2, '0')}-${String(now.getMinutes()).padStart(2, '0')}`;
        const filename = `document_${timestamp}.txt`;

        const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;

        document.body.appendChild(link);
        link.click();

        document.body.removeChild(link);
        URL.revokeObjectURL(url);

    } catch (error) {
        console.error("Download failed:", error);
        document.body.innerHTML = `<div><h1>Error</h1><p>Could not process the file for download. Error: ${error.message}</p></div>`;
    }
});