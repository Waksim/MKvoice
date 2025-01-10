# ---- FILE: Makefile ----

PO_LANGS = en ru uk zh

all: extract init update compile

extract:
	xgettext --language=Python \
	        --keyword=_ \
	        --from-code=UTF-8 \
	        --output=locales/messages.pot \
	        $(shell find . -type f -name "*.py" ! -path "./venv/*" ! -path "./locales/*" ! -path "./.git/*")
	echo "Translation strings extraction completed."

init:
	for lang in $(PO_LANGS); do \
		if [ ! -f "locales/$$lang/LC_MESSAGES/messages.po" ]; then \
			msginit --locale=$$lang \
			        --input=locales/messages.pot \
			        --output-file=locales/$$lang/LC_MESSAGES/messages.po \
			        --no-translator; \
			echo "Created locales/$$lang/LC_MESSAGES/messages.po"; \
		else \
			echo "File locales/$$lang/LC_MESSAGES/messages.po already exists"; \
		fi; \
	done

update:
	for lang in $(PO_LANGS); do \
		msgmerge -U locales/$$lang/LC_MESSAGES/messages.po locales/messages.pot; \
		echo "Updated locales/$$lang/LC_MESSAGES/messages.po"; \
	done

compile:
	bash locales/compile_translations.sh
	echo "Translation compilation completed."

clean:
	rm -f locales/messages.pot

.PHONY: all extract init update compile clean
