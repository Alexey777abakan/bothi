# Скрипт для публикации интеграции с Mistral API на GitHub
$repoUrl = "https://github.com/Alexey777abakan/bothi.git"
$tempDir = "D:\Pit\Publicistorii\bot_project\temp_bothi_mistral"

Write-Host "Начинаю публикацию интеграции с Mistral API на GitHub..."

# Клонируем существующий репозиторий
if (Test-Path $tempDir) {
    Remove-Item -Path $tempDir -Recurse -Force
}
git clone $repoUrl $tempDir

# Перейдем в директорию репозитория
Set-Location $tempDir

# Копируем новые и обновленные файлы
$sourceDir = "D:\Pit\Publicistorii\bot_project\030425"

Write-Host "Копирование новых и обновленных файлов..."

# Новый файл mistral_ai.py
Copy-Item -Path "$sourceDir\mistral_ai.py" -Destination "mistral_ai.py" -Force
Write-Host "Скопирован mistral_ai.py"

# Обновленный файл content_generator.py
Copy-Item -Path "$sourceDir\content_generator.py" -Destination "content_generator.py" -Force
Write-Host "Скопирован content_generator.py"

# Обновленный файл requirements.txt
Copy-Item -Path "$sourceDir\requirements.txt" -Destination "requirements.txt" -Force
Write-Host "Скопирован requirements.txt"

# Обновленный файл .env.example
Copy-Item -Path "$sourceDir\.env.example" -Destination ".env.example" -Force
Write-Host "Скопирован .env.example"

# Обновленный файл render.yaml
Copy-Item -Path "$sourceDir\render.yaml" -Destination "render.yaml" -Force
Write-Host "Скопирован render.yaml"

# Добавляем и коммитим изменения
git add mistral_ai.py
git add content_generator.py
git add requirements.txt
git add .env.example
git add render.yaml

# Настройка Git
git config --local user.name "Alexey777abakan"
git config --local user.email "your-email@example.com"

# Создаем коммит
git commit -m "Добавлена интеграция с Mistral AI API"

# Отправляем изменения на GitHub
Write-Host "Отправка изменений на GitHub..."
git push origin main

# Возвращаемся в исходную директорию
Set-Location "D:\Pit\Publicistorii\bot_project\030425"

Write-Host "Готово! Интеграция с Mistral AI успешно опубликована на GitHub." 