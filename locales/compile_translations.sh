# locales/compile_translations.sh

cd "$(dirname "$0")"

for lang in en ru uk zh; do
    msgfmt "$lang/LC_MESSAGES/messages.po" -o "$lang/LC_MESSAGES/messages.mo"
    echo "Скомпилирован locales/$lang/LC_MESSAGES/messages.mo"
done
