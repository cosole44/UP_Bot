#!/bin/bash

# Настройки
PROJECT_NAME="UP_Bot"
PROJECT_DIR="/opt/$PROJECT_NAME"
GITHUB_REPO="https://github.com/cosole44/UP_Bot.git"
SERVICE_NAME="up_bot.service"
PYTHON_BIN="/usr/bin/python3"
ENV_FILE="$PROJECT_DIR/.env"

# Проверка на root
if [ "$EUID" -ne 0 ]; then
  echo "Пожалуйста, запустите скрипт от root"
  exit 1
fi

# Клонируем репозиторий, если нет
if [ ! -d "$PROJECT_DIR" ]; then
  git clone "$GITHUB_REPO" "$PROJECT_DIR"
else
  echo "Репозиторий уже существует, подтягиваем обновления..."
  cd "$PROJECT_DIR" || exit
  git pull origin main
fi

cd "$PROJECT_DIR" || exit

# Создание .env при первом запуске
if [ ! -f "$ENV_FILE" ]; then
  echo "Файл .env не найден. Нужно ввести данные для бота."
  read -p "Введите BOT_TOKEN: " BOT_TOKEN
  read -p "Введите ADMIN_IDS (через запятую): " ADMIN_IDS
  cat <<EOF > "$ENV_FILE"
BOT_TOKEN='$BOT_TOKEN'
ADMIN_IDS=$ADMIN_IDS
EOF
  echo ".env создан."
fi

# Создаём/обновляем виртуальное окружение
if [ ! -d "venv" ]; then
  $PYTHON_BIN -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

# Создаём systemd-сервис, если нет
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME"
if [ ! -f "$SERVICE_FILE" ]; then
  cat <<EOF > "$SERVICE_FILE"
[Unit]
Description=Telegram bot $PROJECT_NAME
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_DIR
EnvironmentFile=$ENV_FILE
ExecStart=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
  systemctl daemon-reload
  systemctl enable "$SERVICE_NAME"
fi

# Перезапуск сервиса
systemctl restart "$SERVICE_NAME"
echo "Сервис $SERVICE_NAME запущен/обновлён успешно"
