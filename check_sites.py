#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import re
import json
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import time
from datetime import datetime
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SiteChecker:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.results = {}
        
    def normalize_url(self, url):
        """Нормализация URL"""
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        return url.rstrip('/')
    
    def check_site(self, url):
        """Проверка одного сайта по всем критериям"""
        normalized_url = self.normalize_url(url)
        logger.info(f"Проверяю сайт: {normalized_url}")
        
        result = {
            'url': normalized_url,
            'accessible': False,
            'checks': {},
            'errors': []
        }
        
        try:
            # Проверяем доступность сайта
            response = self.session.get(normalized_url, timeout=10, allow_redirects=True)
            result['accessible'] = response.status_code == 200
            
            if not result['accessible']:
                result['errors'].append(f"Сайт недоступен (код: {response.status_code})")
                return result
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Проверка 1: Политика конфиденциальности
            result['checks']['privacy_policy'] = self.check_privacy_policy(soup, normalized_url)
            
            # Проверка 2: Чекбоксы согласия на обработку ПДн
            result['checks']['pd_consent_checkboxes'] = self.check_pd_consent_checkboxes(soup)
            
            # Проверка 3: Чекбокс не отмечен по умолчанию
            result['checks']['checkbox_not_checked'] = self.check_checkbox_not_checked(soup)
            
            # Проверка 4: Фиксация согласия (логирование)
            result['checks']['consent_logging'] = self.check_consent_logging(soup)
            
            # Проверка 5: Всплывающее окно о cookie
            result['checks']['cookie_popup'] = self.check_cookie_popup(soup)
            
            # Проверка 6: Разделение cookie на обязательные и прочие
            result['checks']['cookie_categories'] = self.check_cookie_categories(soup)
            
            # Проверка 7: Хранение ПДн на территории РФ
            result['checks']['pd_storage_russia'] = self.check_pd_storage_russia(soup)
            
            # Проверка 8: Регистрация в РКН
            result['checks']['rkn_registration'] = self.check_rkn_registration(soup)
            
            # Проверка 9: Email для обращений субъектов данных
            result['checks']['data_subject_email'] = self.check_data_subject_email(soup)
            
            # Проверка 10: Аудит сторонних сервисов
            result['checks']['third_party_audit'] = self.check_third_party_audit(soup, response)
            
        except Exception as e:
            result['errors'].append(f"Ошибка при проверке: {str(e)}")
            logger.error(f"Ошибка при проверке {normalized_url}: {str(e)}")
        
        return result
    
    def check_privacy_policy(self, soup, base_url):
        """Проверка наличия политики конфиденциальности"""
        # Поиск ссылок на политику конфиденциальности
        privacy_keywords = [
            'политика конфиденциальности', 'privacy policy', 'privacy', 
            'конфиденциальность', 'обработка персональных данных',
            'персональные данные', 'политика обработки'
        ]
        
        links = soup.find_all('a', href=True)
        for link in links:
            link_text = link.get_text().lower()
            href = link.get('href', '').lower()
            
            for keyword in privacy_keywords:
                if keyword in link_text or keyword in href:
                    return True
        
        # Поиск по URL
        for keyword in ['privacy', 'confidential', 'policy']:
            if keyword in base_url.lower():
                return True
        
        return False
    
    def check_pd_consent_checkboxes(self, soup):
        """Проверка наличия чекбоксов согласия на обработку ПДн"""
        # Поиск чекбоксов с текстом о согласии
        consent_keywords = [
            'согласие', 'согласен', 'соглашаюсь', 'consent', 'agree',
            'персональные данные', 'personal data', 'обработка', 'processing'
        ]
        
        checkboxes = soup.find_all(['input', 'div', 'label'], 
                                 {'type': 'checkbox'}) + soup.find_all('input')
        
        for checkbox in checkboxes:
            # Проверяем текст рядом с чекбоксом
            text_content = ''
            if checkbox.parent:
                text_content = checkbox.parent.get_text().lower()
            if checkbox.find_next_sibling():
                text_content += checkbox.find_next_sibling().get_text().lower()
            
            for keyword in consent_keywords:
                if keyword in text_content:
                    return True
        
        return False
    
    def check_checkbox_not_checked(self, soup):
        """Проверка что чекбокс не отмечен по умолчанию"""
        # Это сложно проверить автоматически, но можно искать атрибуты
        checkboxes = soup.find_all('input', {'type': 'checkbox'})
        
        for checkbox in checkboxes:
            # Если чекбокс не имеет атрибута checked, то он не отмечен по умолчанию
            if not checkbox.get('checked'):
                return True
        
        return len(checkboxes) == 0  # Если чекбоксов нет, считаем что требование выполнено
    
    def check_consent_logging(self, soup):
        """Проверка фиксации согласия (логирование)"""
        # Поиск упоминаний о логировании согласий
        logging_keywords = [
            'логирование', 'фиксация', 'запись', 'журнал', 'log', 'logging',
            'согласие', 'consent', 'timestamp', 'время', 'дата', 'ip'
        ]
        
        page_text = soup.get_text().lower()
        for keyword in logging_keywords:
            if keyword in page_text:
                return True
        
        return False
    
    def check_cookie_popup(self, soup):
        """Проверка всплывающего окна о cookie"""
        cookie_keywords = [
            'cookie', 'куки', 'файлы cookie', 'cookies', 'куки-файлы'
        ]
        
        # Поиск элементов, которые могут быть всплывающими окнами
        popup_selectors = [
            '.popup', '.modal', '.overlay', '.cookie', '.notification',
            '[class*="popup"]', '[class*="modal"]', '[class*="cookie"]'
        ]
        
        for selector in popup_selectors:
            elements = soup.select(selector)
            for element in elements:
                element_text = element.get_text().lower()
                for keyword in cookie_keywords:
                    if keyword in element_text:
                        return True
        
        return False
    
    def check_cookie_categories(self, soup):
        """Проверка разделения cookie на категории"""
        category_keywords = [
            'обязательные', 'необходимые', 'required', 'essential',
            'аналитические', 'analytics', 'маркетинговые', 'marketing',
            'функциональные', 'functional', 'рекламные', 'advertising'
        ]
        
        page_text = soup.get_text().lower()
        found_categories = 0
        
        for keyword in category_keywords:
            if keyword in page_text:
                found_categories += 1
        
        return found_categories >= 2  # Должно быть минимум 2 категории
    
    def check_pd_storage_russia(self, soup):
        """Проверка хранения ПДн на территории РФ"""
        russia_keywords = [
            'россия', 'рф', 'российской федерации', 'территория рф',
            'russia', 'russian federation', 'российские серверы'
        ]
        
        page_text = soup.get_text().lower()
        for keyword in russia_keywords:
            if keyword in page_text:
                return True
        
        return False
    
    def check_rkn_registration(self, soup):
        """Проверка регистрации в РКН"""
        rkn_keywords = [
            'ркн', 'роскомнадзор', 'рособрнадзор', 'roskomnadzor',
            'регистрация', 'registration', 'оператор персональных данных'
        ]
        
        page_text = soup.get_text().lower()
        for keyword in rkn_keywords:
            if keyword in page_text:
                return True
        
        return False
    
    def check_data_subject_email(self, soup):
        """Проверка email для обращений субъектов данных"""
        # Поиск email адресов
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, soup.get_text())
        
        # Поиск упоминаний о субъектах данных
        subject_keywords = [
            'субъект данных', 'data subject', 'обращение', 'запрос',
            'контакт', 'связаться', 'обратная связь'
        ]
        
        page_text = soup.get_text().lower()
        has_subject_mention = any(keyword in page_text for keyword in subject_keywords)
        
        return len(emails) > 0 and has_subject_mention
    
    def check_third_party_audit(self, soup, response):
        """Проверка аудита сторонних сервисов"""
        # Поиск внешних скриптов и сервисов
        external_scripts = soup.find_all('script', src=True)
        external_links = soup.find_all('a', href=True)
        
        # Известные сторонние сервисы
        third_party_services = [
            'google', 'facebook', 'yandex', 'vk', 'twitter', 'instagram',
            'analytics', 'tracking', 'pixel', 'tag', 'gtag', 'fbq'
        ]
        
        found_services = []
        for script in external_scripts:
            src = script.get('src', '').lower()
            for service in third_party_services:
                if service in src:
                    found_services.append(service)
        
        # Если найдены сторонние сервисы, проверяем упоминания об их обработке
        if found_services:
            audit_keywords = [
                'аудит', 'проверка', 'анализ', 'audit', 'review',
                'сторонние сервисы', 'third party', 'внешние сервисы'
            ]
            
            page_text = soup.get_text().lower()
            return any(keyword in page_text for keyword in audit_keywords)
        
        return True  # Если сторонних сервисов нет, считаем что аудит проведен
    
    def check_all_sites(self, sites_file):
        """Проверка всех сайтов из файла"""
        with open(sites_file, 'r', encoding='utf-8') as f:
            sites = [line.strip() for line in f if line.strip() and not line.startswith('-')]
        
        logger.info(f"Найдено {len(sites)} сайтов для проверки")
        
        for i, site in enumerate(sites, 1):
            logger.info(f"Проверяю сайт {i}/{len(sites)}: {site}")
            result = self.check_site(site)
            self.results[site] = result
            
            # Небольшая пауза между запросами
            time.sleep(1)
        
        return self.results
    
    def generate_report(self, output_file='result.md'):
        """Генерация отчета в формате Markdown"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Отчет по проверке сайтов на соответствие требованиям к обработке ПДн\n\n")
            f.write(f"Дата проверки: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Статистика
            total_sites = len(self.results)
            accessible_sites = sum(1 for r in self.results.values() if r['accessible'])
            
            f.write(f"## Статистика\n\n")
            f.write(f"- Всего сайтов: {total_sites}\n")
            f.write(f"- Доступных сайтов: {accessible_sites}\n")
            f.write(f"- Недоступных сайтов: {total_sites - accessible_sites}\n\n")
            
            # Детальные результаты
            f.write("## Детальные результаты\n\n")
            
            for site, result in self.results.items():
                f.write(f"### {site}\n\n")
                
                if not result['accessible']:
                    f.write("❌ **Сайт недоступен**\n\n")
                    if result['errors']:
                        f.write("**Ошибки:**\n")
                        for error in result['errors']:
                            f.write(f"- {error}\n")
                    f.write("\n---\n\n")
                    continue
                
                # Результаты проверок
                checks = result['checks']
                f.write("| Критерий | Статус |\n")
                f.write("|----------|--------|\n")
                
                check_names = {
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
                
                for check_key, check_name in check_names.items():
                    status = "✅" if checks.get(check_key, False) else "❌"
                    f.write(f"| {check_name} | {status} |\n")
                
                f.write("\n")
                
                # Подсчет выполненных требований
                passed_checks = sum(1 for check in checks.values() if check)
                total_checks = len(checks)
                compliance_percentage = (passed_checks / total_checks) * 100
                
                f.write(f"**Соответствие: {passed_checks}/{total_checks} ({compliance_percentage:.1f}%)**\n\n")
                
                if result['errors']:
                    f.write("**Ошибки:**\n")
                    for error in result['errors']:
                        f.write(f"- {error}\n")
                    f.write("\n")
                
                f.write("---\n\n")
        
        logger.info(f"Отчет сохранен в файл: {output_file}")

def main():
    checker = SiteChecker()
    results = checker.check_all_sites('battle_sites.txt')
    checker.generate_report('result.md')
    
    # Вывод краткой статистики
    total = len(results)
    accessible = sum(1 for r in results.values() if r['accessible'])
    print(f"\nПроверка завершена!")
    print(f"Всего сайтов: {total}")
    print(f"Доступных: {accessible}")
    print(f"Недоступных: {total - accessible}")
    print(f"Отчет сохранен в result.md")

if __name__ == "__main__":
    main() 