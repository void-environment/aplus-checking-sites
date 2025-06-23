import json

# Чтение JSON файла
with open('sites.json', 'r', encoding='utf-8') as file:
    data = json.load(file)  # data - это список

# Извлечение всех ссылок из поля "Боевой сайт"
battle_sites = []
for item in data:
    if isinstance(item, dict):  # Проверяем, что элемент является словарем
        url = item.get("Боевой сайт", "")
        if url:  # Если ссылка не пустая
            battle_sites.append(url)

# Запись ссылок в текстовый файл
with open('battle_sites.txt', 'w', encoding='utf-8') as output_file:
    for url in battle_sites:
        output_file.write(url + '\n')

print(f"Успешно записано {len(battle_sites)} ссылок в battle_sites.txt")