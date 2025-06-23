#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from collections import defaultdict

def analyze_results():
    """Анализ результатов проверки"""
    
    with open('result.md', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Извлечение статистики
    stats_match = re.search(r'Всего сайтов: (\d+)\n- Доступных сайтов: (\d+)\n- Недоступных сайтов: (\d+)', content)
    total_sites = int(stats_match.group(1))
    accessible_sites = int(stats_match.group(2))
    inaccessible_sites = int(stats_match.group(3))
    
    # Поиск всех результатов соответствия
    compliance_pattern = r'Соответствие: (\d+)/(\d+) \((\d+\.\d+)%\)'
    compliance_matches = re.findall(compliance_pattern, content)
    
    # Анализ по критериям
    criteria_stats = defaultdict(int)
    criteria_names = {
        'privacy_policy': '1. Политика конфиденциальности',
        'pd_consent_checkboxes': '2. Чекбоксы согласия на обработку ПДн',
        'checkbox_not_checked': '3. Чекбокс не отмечен по умолчанию',
        'consent_logging': '4. Фиксация согласия (логирование)',
        'cookie_popup': '5. Всплывающее окно о cookie',
        'cookie_categories': '6. Разделение cookie на категории',
        'pd_storage_russia': '7. Хранение ПДн на территории РФ',
        'rkn_registration': '8. Регистрация в РКН',
        'data_subject_email': '9. Email для обращений субъектов данных',
        'third_party_audit': '10. Аудит сторонних сервисов'
    }
    
    # Поиск статусов по каждому критерию
    for i, (criteria_key, criteria_name) in enumerate(criteria_names.items(), 1):
        pattern = rf'{re.escape(criteria_name)} \| (✅|❌)'
        matches = re.findall(pattern, content)
        criteria_stats[criteria_key] = {
            'passed': matches.count('✅'),
            'failed': matches.count('❌'),
            'total': len(matches)
        }
    
    # Создание краткого резюме
    with open('summary.md', 'w', encoding='utf-8') as f:
        f.write("# Краткое резюме проверки сайтов на соответствие требованиям к обработке ПДн\n\n")
        
        f.write("## Общая статистика\n\n")
        f.write(f"- **Всего проверено сайтов:** {total_sites}\n")
        f.write(f"- **Доступных сайтов:** {accessible_sites} ({accessible_sites/total_sites*100:.1f}%)\n")
        f.write(f"- **Недоступных сайтов:** {inaccessible_sites} ({inaccessible_sites/total_sites*100:.1f}%)\n\n")
        
        # Статистика соответствия
        if compliance_matches:
            compliance_scores = [float(match[2]) for match in compliance_matches]
            avg_compliance = sum(compliance_scores) / len(compliance_scores)
            max_compliance = max(compliance_scores)
            min_compliance = min(compliance_scores)
            
            f.write("## Статистика соответствия\n\n")
            f.write(f"- **Среднее соответствие:** {avg_compliance:.1f}%\n")
            f.write(f"- **Максимальное соответствие:** {max_compliance:.1f}%\n")
            f.write(f"- **Минимальное соответствие:** {min_compliance:.1f}%\n\n")
            
            # Распределение по уровням соответствия
            excellent = len([s for s in compliance_scores if s >= 80])
            good = len([s for s in compliance_scores if 60 <= s < 80])
            fair = len([s for s in compliance_scores if 40 <= s < 60])
            poor = len([s for s in compliance_scores if s < 40])
            
            f.write("### Распределение по уровням соответствия\n\n")
            f.write(f"- **Отлично (80-100%):** {excellent} сайтов ({excellent/len(compliance_scores)*100:.1f}%)\n")
            f.write(f"- **Хорошо (60-79%):** {good} сайтов ({good/len(compliance_scores)*100:.1f}%)\n")
            f.write(f"- **Удовлетворительно (40-59%):** {fair} сайтов ({fair/len(compliance_scores)*100:.1f}%)\n")
            f.write(f"- **Плохо (0-39%):** {poor} сайтов ({poor/len(compliance_scores)*100:.1f}%)\n\n")
        
        # Анализ по критериям
        f.write("## Анализ по критериям\n\n")
        f.write("| Критерий | Выполнено | Не выполнено | Процент выполнения |\n")
        f.write("|----------|-----------|--------------|-------------------|\n")
        
        for criteria_key, criteria_name in criteria_names.items():
            stats = criteria_stats[criteria_key]
            if stats['total'] > 0:
                percentage = (stats['passed'] / stats['total']) * 100
                f.write(f"| {criteria_name} | {stats['passed']} | {stats['failed']} | {percentage:.1f}% |\n")
        
        f.write("\n")
        
        # Топ-5 лучших сайтов
        f.write("## Топ-5 сайтов с наилучшим соответствием\n\n")
        site_compliance = []
        
        # Поиск сайтов и их соответствия
        site_pattern = r'### (https?://[^\n]+)\n\n.*?Соответствие: (\d+)/(\d+) \((\d+\.\d+)%\)'
        site_matches = re.findall(site_pattern, content, re.DOTALL)
        
        for match in site_matches:
            site_url = match[0]
            percentage = float(match[3])
            site_compliance.append((site_url, percentage))
        
        # Сортировка по убыванию соответствия
        site_compliance.sort(key=lambda x: x[1], reverse=True)
        
        for i, (site_url, percentage) in enumerate(site_compliance[:5], 1):
            f.write(f"{i}. **{site_url}** - {percentage:.1f}%\n")
        
        f.write("\n")
        
        # Основные проблемы
        f.write("## Основные проблемы\n\n")
        
        # Находим критерии с наименьшим процентом выполнения
        criteria_percentages = []
        for criteria_key, criteria_name in criteria_names.items():
            stats = criteria_stats[criteria_key]
            if stats['total'] > 0:
                percentage = (stats['passed'] / stats['total']) * 100
                criteria_percentages.append((criteria_name, percentage))
        
        criteria_percentages.sort(key=lambda x: x[1])
        
        f.write("### Критерии с наименьшим процентом выполнения:\n\n")
        for criteria_name, percentage in criteria_percentages[:3]:
            f.write(f"- **{criteria_name}** - {percentage:.1f}%\n")
        
        f.write("\n")
        
        # Рекомендации
        f.write("## Рекомендации\n\n")
        f.write("### Приоритетные направления для улучшения:\n\n")
        
        recommendations = {
            'cookie_categories': 'Внедрить разделение cookie на обязательные и прочие категории с возможностью выбора пользователем',
            'rkn_registration': 'Проверить необходимость регистрации в РКН как оператора персональных данных',
            'cookie_popup': 'Добавить всплывающее окно с информацией о cookie-файлах',
            'pd_consent_checkboxes': 'Добавить чекбоксы согласия на обработку персональных данных во все формы',
            'third_party_audit': 'Провести аудит взаимодействия со сторонними сервисами и документировать его результаты',
            'pd_storage_russia': 'Убедиться, что персональные данные хранятся на серверах в РФ',
            'data_subject_email': 'Добавить контактную информацию для обращений субъектов персональных данных',
            'privacy_policy': 'Разработать и опубликовать актуальную политику конфиденциальности',
            'consent_logging': 'Реализовать систему логирования согласий пользователей',
            'checkbox_not_checked': 'Убедиться, что чекбоксы согласия не отмечены по умолчанию'
        }
        
        for criteria_name, percentage in criteria_percentages[:5]:
            criteria_key = next(k for k, v in criteria_names.items() if v == criteria_name)
            if criteria_key in recommendations:
                f.write(f"- **{criteria_name}** ({percentage:.1f}%): {recommendations[criteria_key]}\n")
        
        f.write("\n")
        f.write("### Общие рекомендации:\n\n")
        f.write("1. **Провести комплексный аудит** соответствия требованиям 152-ФЗ\n")
        f.write("2. **Разработать план мероприятий** по приведению в соответствие\n")
        f.write("3. **Назначить ответственного** за обработку персональных данных\n")
        f.write("4. **Провести обучение персонала** по вопросам защиты персональных данных\n")
        f.write("5. **Регулярно проводить мониторинг** соответствия требованиям\n")
    
    print("Анализ завершен! Краткое резюме сохранено в summary.md")

if __name__ == "__main__":
    analyze_results() 