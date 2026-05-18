#!/bin/bash
set -e  # раскоментить, чтобы остановить выполнение при ошибке

echo "=== Сливаем основной проект... ==="
git pull
echo

MODULES_DIR="./src/modules"

if [ ! -d "$MODULES_DIR" ]; then
    echo "Ошибка: папка $MODULES_DIR не найдена!"
    exit 1
fi

cd "$MODULES_DIR"

echo "=== Обновляем модули ==="

for dir in */; do
    if [ -d "$dir/.git" ]; then
        echo "--- $dir ---"
        cd "$dir"
        git pull || echo "⚠️ Ошибка при pull в $dir"
        cd ..
    else
        echo "⏭ Пропускаем $dir (не git-репозиторий)"
    fi
done

echo
echo "✅ Все модули обновлены!"
