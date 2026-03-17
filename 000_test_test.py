import os
import time
import pytest
import math
import socket
from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput


def retry_find_element(driver, by, value, timeout=30, poll=3):
    """Повторный поиск элемента с интервалами"""
    end = time.time() + timeout
    while time.time() < end:
        try:
            element = driver.find_element(by, value)
            if element and element.is_displayed():
                return element
        except (NoSuchElementException, StaleElementReferenceException):
            pass
        time.sleep(poll)
    return None


def swipe_right(driver, swipe_button, duration=800):
    """Свайп вправо для слайдера"""
    start_x = swipe_button.rect['x']
    start_y = swipe_button.rect['y'] + swipe_button.rect['height'] // 2
    end_x = swipe_button.rect['x'] + swipe_button.rect['width'] * 5
    end_y = start_y
    actions = ActionBuilder(driver)
    finger = actions.add_pointer_input("touch", "finger1")
    finger.create_pointer_move(duration=0, x=start_x, y=start_y, origin='viewport')
    finger.create_pointer_down(button=0)
    finger.create_pointer_move(duration=duration, x=end_x, y=end_y, origin='viewport')
    finger.create_pointer_up(button=0)
    actions.perform()


def click_until_disappears(element, timeout=5, interval=0.5):
    """
    Кликает по элементу, пока он отображается, или пока не истечет таймаут.
    """
    if not element:
        return

    start = time.time()
    while True:
        try:
            if not element or not element.is_displayed():
                break
            element.click()
        except StaleElementReferenceException:
            break
        except Exception:
            break
        if time.time() - start > timeout:
            break
        time.sleep(interval)


def tap_by_coordinates(driver, x, y):
    """Тап по координатам"""
    actions = ActionBuilder(driver)
    finger = actions.add_pointer_input("touch", "finger1")
    finger.create_pointer_move(duration=0, x=x, y=y, origin='viewport')
    finger.create_pointer_down(button=0)
    finger.create_pointer_up(button=0)
    actions.perform()


def wait_for_activity(driver, activity: str, timeout=60):
    """Ожидание загрузки указанной активности"""
    if not driver.wait_activity(activity, timeout):
        raise AssertionError(f"Активность {activity} не загрузилась за {timeout} секунд")


def country_selector_opened(driver):
    """Проверка, открылось ли окно выбора страны"""
    try:
        retry_find_element(driver, AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("United States")')
        return True
    except AssertionError:
        return False


def safe_get_current_activity(driver):
    """Безопасный вызов current_activity"""
    try:
        return driver.current_activity
    except Exception as e:
        return f"<ошибка получения activity: {e}>"


def safe_get_current_package(driver):
    """Безопасный вызов current_package"""
    try:
        return driver.current_package
    except Exception as e:
        return f"<ошибка получения package: {e}>"


def click_until_gone(driver, by, value, attempts=30):
    """Клик по элементу пока он не исчезнет"""
    for _ in range(attempts):
        try:
            el = retry_find_element(driver, by, value, timeout=5, poll=1)
            if el:
                el.click()
                time.sleep(1)
            else:
                return True
        except StaleElementReferenceException:
            continue
        except Exception:
            continue
    return True  # Возвращаем True даже если не нашли, так как элемент мог уже исчезнуть


def select_country(driver, country_name="Russia"):
    """Выбор страны"""
    if not retry_find_element(driver,
                              AppiumBy.XPATH,
                              "//android.widget.EditText[@resource-id='PhoneInput']", timeout=100, poll=5):
        raise AssertionError(f"select_country: элемент PhoneInput не найден")

    search_input = retry_find_element(
        driver,
        AppiumBy.XPATH,
        "//android.view.ViewGroup[@resource-id='CountryCodeList']"
    )
    if not search_input:
        raise AssertionError("Не найден элемент выбора страны")
    search_input.click()
    time.sleep(1)

    search_input = retry_find_element(
        driver,
        AppiumBy.XPATH,
        "//android.widget.EditText[@text='Search for a country']"
    )
    if not search_input:
        raise AssertionError("Не найдено поле поиска страны")
    search_input.click()
    search_input.send_keys(country_name)

    # Enter и пауза
    driver.press_keycode(66)  # KEYCODE_ENTER
    time.sleep(2)

    # Кликаем по текстовому элементу, исключая поле ввода
    country_element = retry_find_element(
        driver,
        AppiumBy.XPATH,
        f"//android.widget.TextView[@text='{country_name}']",
        timeout=10
    )
    if not country_element:
        raise AssertionError(f"Не найдена страна {country_name}")
    country_element.click()
    time.sleep(1)

def close_update_modal_if_present(driver, checks=3):
    print("🔍 Проверяем наличие модального окна с обновлением...")

    for attempt in range(checks):

        close_button = retry_find_element(
            driver,
            AppiumBy.XPATH,
            "//android.view.ViewGroup[@resource-id='NotifyUpdatesSoftModalCloseCloseButton']",
            timeout=3,
            poll=1
        )

        if close_button and close_button.is_displayed():
            print("✅ Найдена модалка обновления, закрываем...")

            try:
                close_button.click()
                time.sleep(1)
                print("✅ Модалка закрыта через кнопку")
                return True

            except Exception as e:
                print(f"⚠️ Клик по кнопке не сработал: {e}")

                try:
                    tap_by_coordinates(driver, 900, 480)
                    time.sleep(1)
                    print("✅ Модалка закрыта через координаты")
                    return True

                except Exception as e:
                    print(f"⚠️ Не удалось закрыть модалку: {e}")

        print(f"ℹ️ Попытка {attempt + 1}: модалка не найдена")
        time.sleep(2)

    print("✅ Модальное окно не появилось")
    return False

def login_with_phone(driver, phone_number="9310000306", password="A!23456789z"):
    """Авторизация по телефону"""
    print("📱 Начинаем авторизацию...")

    # Ждём поле ввода телефона
    input_field = retry_find_element(
        driver,
        AppiumBy.XPATH,
        "//android.widget.EditText[@resource-id='PhoneInput']",
        timeout=60
    )
    if not input_field:
        raise AssertionError("Не найдено поле ввода телефона")

    input_field.click()
    input_field.send_keys(phone_number)
    time.sleep(1)
    driver.hide_keyboard()
    time.sleep(1)

    # Кнопка продолжения с телефоном
    button = retry_find_element(
        driver,
        AppiumBy.XPATH,
        "//android.view.ViewGroup[@resource-id='PhoneSign']",
        timeout=30
    )
    if not button:
        raise AssertionError("Не найдена кнопка PhoneSign")
    button.click()
    time.sleep(2)
    button.click()  # Двойной клик для надёжности
    time.sleep(2)

    # Поле ввода пароля
    password_field = retry_find_element(
        driver,
        AppiumBy.XPATH,
        '//android.widget.EditText[@password="true"]',
        timeout=30
    )
    if not password_field:
        raise AssertionError("Не найдено поле ввода пароля")

    password_field.click()
    password_field.send_keys(password)
    time.sleep(1)
    driver.hide_keyboard()
    time.sleep(1)

    # Кнопка подтверждения пароля
    next_button = retry_find_element(
        driver,
        AppiumBy.XPATH,
        "//android.view.ViewGroup[@resource-id='PasswordSubmit']",
        timeout=30
    )
    if not next_button:
        raise AssertionError("Не найдена кнопка PasswordSubmit")

    click_until_disappears(next_button, timeout=10)
    time.sleep(3)  # Ждём появления модалок

    # ПРОВЕРКА МОДАЛЬНОГО ОКНА С ОБНОВЛЕНИЕМ
    close_update_modal_if_present(driver)

    # Кнопка Dismiss (если есть)
    close_button = retry_find_element(
        driver,
        AppiumBy.ACCESSIBILITY_ID,
        "Dismiss",
        timeout=5
    )
    if close_button:
        print("✅ Найдена кнопка Dismiss, закрываем...")
        close_button.click()
        time.sleep(2)

    # Кнопка оптимизации батареи (если есть)
    optimize_button = retry_find_element(
        driver,
        AppiumBy.XPATH,
        "//android.view.ViewGroup[@resource-id='TripAutoStartAndStopPermissionModalAllowBatteryOptimization']",
        timeout=5
    )
    if optimize_button:
        print("✅ Найдена кнопка оптимизации батареи, нажимаем...")
        optimize_button.click()
        time.sleep(2)

    # Системные диалоги
    click_until_gone(driver, AppiumBy.ID, "android:id/button1")
    click_until_gone(driver, AppiumBy.ID, "android:id/button1")

    # Финальная проверка модального окна
    time.sleep(2)
    close_update_modal_if_present(driver)

    print("✅ Авторизация завершена")


def start_stop_drive(driver):
    """Запуск и остановка поездки"""
    print("🚗 Начинаем процесс поездки...")

    # Проверяем модальное окно перед началом
    close_update_modal_if_present(driver)
    time.sleep(2)

    # Кнопка начала поездки
    drive_button = retry_find_element(
        driver,
        AppiumBy.XPATH,
        '(//android.view.View[@clickable="true"])[2]',
        timeout=60
    )
    if not drive_button:
        # Проверяем модалку ещё раз
        close_update_modal_if_present(driver)
        drive_button = retry_find_element(
            driver,
            AppiumBy.XPATH,
            '(//android.view.View[@clickable="true"])[2]',
            timeout=30
        )
        if not drive_button:
            raise AssertionError("Не найдена кнопка начала поездки")

    drive_button.click()
    print("✅ Кнопка начала поездки нажата")
    time.sleep(3)

    # Кнопка "Принять"
    accept_button = retry_find_element(
        driver,
        AppiumBy.ACCESSIBILITY_ID,
        "Принять",
        timeout=30
    )
    if not accept_button:
        # Если не нашли - возможно, появилась модалка с обновлением
        close_update_modal_if_present(driver)
        accept_button = retry_find_element(
            driver,
            AppiumBy.ACCESSIBILITY_ID,
            "Принять",
            timeout=20
        )
        if not accept_button:
            raise AssertionError("Не найдена кнопка 'Принять'")

    accept_button.click()
    print("✅ Кнопка 'Принять' нажата")
    time.sleep(3)

    # Слайдер старта поездки
    swipe_button = retry_find_element(
        driver,
        AppiumBy.XPATH,
        "//android.view.ViewGroup[@resource-id='StartTripSlider']",
        timeout=30
    )
    if not swipe_button:
        raise AssertionError("Не найден слайдер старта поездки")

    swipe_right(driver, swipe_button)
    print("✅ Слайдер старта поездки активирован")
    time.sleep(3)

    # Реагируем на незавершённую предыдущую поездку
    stop_previous_drive = retry_find_element(
        driver,
        AppiumBy.XPATH,
        "//android.view.ViewGroup[@resource-id='StopPreviousTripModalAccept']",
        timeout=10
    )
    if stop_previous_drive:
        print("⚠️ Обнаружена предыдущая поездка, завершаем...")
        stop_previous_drive.click()
        time.sleep(3)

    # Едем 30 секунд
    print("⏳ Поездка в процессе... 30 секунд")
    time.sleep(30)

    # Слайдер остановки поездки
    swipe_button = retry_find_element(
        driver,
        AppiumBy.XPATH,
        "//android.view.ViewGroup[@resource-id='TripStopSlider']",
        timeout=90
    )
    if not swipe_button:
        raise AssertionError("Не найден слайдер остановки поездки")

    swipe_right(driver, swipe_button)
    print("✅ Слайдер остановки поездки активирован")
    time.sleep(3)

    # Кнопка завершения поездки
    finish_submit_button = retry_find_element(
        driver,
        AppiumBy.XPATH,
        "//android.view.ViewGroup[@resource-id='TripFinishSubmit']",
        timeout=90
    )
    if not finish_submit_button:
        raise AssertionError("Не найдена кнопка завершения поездки")

    finish_submit_button.click()
    print("✅ Поездка завершена")
    time.sleep(5)


def navigate_to_statistics_screen(driver):
    """Навигация к экрану статистики"""
    print("📍 Навигация к статистике...")

    # Таб статистики
    stats_tab = retry_find_element(
        driver,
        AppiumBy.XPATH,
        '(//android.view.View[@clickable="true"])[3]',
        timeout=30
    )
    if not stats_tab:
        raise AssertionError("Не найден таб статистики")
    stats_tab.click()
    time.sleep(3)

    # Кнопка информации о дистанции
    distance_info = retry_find_element(
        driver,
        AppiumBy.XPATH,
        "//android.view.ViewGroup[@resource-id='TouchableDistanceInfo']",
        timeout=90
    )
    if not distance_info:
        raise AssertionError("Не найдена кнопка TouchableDistanceInfo")
    distance_info.click()
    time.sleep(2)

    # Карточка поездки
    drive_card = retry_find_element(
        driver,
        AppiumBy.XPATH,
        "(//android.view.ViewGroup[@resource-id='DriveStatisticCard'])[1]",
        timeout=30
    )
    if not drive_card:
        raise AssertionError("Не найдена карточка поездки")
    drive_card.click()
    time.sleep(3)

    # Кнопка открытия карты маршрута
    map_button = retry_find_element(
        driver,
        AppiumBy.XPATH,
        "//android.view.ViewGroup[@resource-id='TripStatisticRouteMapOpen']",
        timeout=90
    )
    if not map_button:
        raise AssertionError("Не найдена кнопка открытия карты")
    map_button.click()
    time.sleep(3)

    print("✅ Навигация к статистике завершена")


def check_drive_stats_once(driver):
    """Одиночная проверка статистики (без навигации)"""
    text_elements = driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.TextView")
    if not text_elements:
        return False, "Не найдены текстовые элементы на экране"

    km_values = []
    for i in range(len(text_elements) - 1):
        current_text = text_elements[i].text.strip()
        next_text = text_elements[i + 1].text.strip()
        if next_text == "км":
            try:
                # Очищаем текст от пробелов и заменяем запятую на точку
                clean_text = current_text.replace(" ", "").replace(",", ".")
                value = float(clean_text)
                km_values.append(value)
            except ValueError:
                continue

    if not km_values:
        return False, "Не найдены числовые значения километров"

    valid_values = [value for value in km_values if value > 0]
    if valid_values:
        print(f"✅ Найдены валидные значения > 0: {valid_values}")
        return True, f"Валидные значения: {valid_values}"
    else:
        print(f"❌ Все найденные значения равны 0: {km_values}")
        return False, f"Все значения километров равны 0. Найдено: {km_values}"


def check_drive_stats_with_retry(driver, max_wait_minutes=12, poll_interval_seconds=30):
    """
    Поллинг статистики с повторным открытием экрана при нулевых значениях
    """
    print(f"🔄 Начинаем поллинг статистики: каждые {poll_interval_seconds} секунд, максимум {max_wait_minutes} минут")

    max_wait_seconds = max_wait_minutes * 60
    start_time = time.time()
    attempts = 0
    successful_attempts = 0

    while time.time() - start_time < max_wait_seconds:
        attempts += 1
        elapsed_minutes = (time.time() - start_time) / 60

        print(f"\n🔄 Попытка #{attempts}, прошло {elapsed_minutes:.1f} минут")

        try:

            # 1. Переходим на экран статистики поездки
            print("📍 Переходим на экран статистики...")
            navigate_to_statistics_screen(driver)
            time.sleep(3)  # Даём время для загрузки

            # 2. Проверяем статистику
            success, message = check_drive_stats_once(driver)

            if success:
                successful_attempts += 1
                print(f"✅ Проверка #{attempts} УСПЕШНА через {elapsed_minutes:.1f} минут")
                print(f"✅ Всего успешных проверок: {successful_attempts}")
                return True

            print(f"❌ Проверка #{attempts} НЕУСПЕШНА: {message}")

            # 3. Если данные нулевые - возвращаемся назад для обновления
            if time.time() - start_time + poll_interval_seconds < max_wait_seconds:
                print("↩️  Возвращаемся назад для обновления данных...")
                driver.back()  # Возврат на предыдущий экран
                time.sleep(2)

                # 4. Ждём перед следующей попыткой
                wait_time = poll_interval_seconds - 2  # Минус время на возврат
                if wait_time > 0:
                    print(f"⏳ Ждём {wait_time} секунд до следующей попытки...")
                    time.sleep(wait_time)
            else:
                break

        except Exception as e:
            print(f"⚠️  Ошибка при проверке #{attempts}: {e}")

            # При ошибке тоже пытаемся вернуться и продолжить
            try:
                driver.back()
                time.sleep(2)
            except:
                pass

            if time.time() - start_time + poll_interval_seconds < max_wait_seconds:
                time.sleep(poll_interval_seconds)

    # Если дошли сюда - время вышло
    elapsed_total = (time.time() - start_time) / 60
    raise AssertionError(
        f"❌ За {elapsed_total:.1f} минут валидные данные не появились.\n"
        f"   Всего попыток: {attempts}\n"
        f"   Успешных попыток: {successful_attempts}\n"
        f"   Максимальное время ожидания ({max_wait_minutes} минут) истекло."
    )


def test_app(driver):
    """Основной тест"""
    print("\n🚀 ЗАПУСК ТЕСТА")
    print("=" * 50)

    phone_number = "9310000306"
    password = "A!23456789z"

    # Определяем ветку и выбираем страну если нужно
    current_branch = os.getenv("CI_COMMIT_BRANCH", "local")
    print(f"📌 Текущая ветка: {current_branch}")

    if current_branch in ["global", "main"]:
        print("🌍 Выбираем страну Russia...")
        select_country(driver)
        password = "Exbxic81*"
        print(f"🔑 Используем пароль для {current_branch}")

    # Авторизация
    login_with_phone(driver, phone_number=phone_number, password=password)

    # Дополнительная проверка модального окна на всякий случай
    time.sleep(3)
    close_update_modal_if_present(driver)

    # Запуск и остановка поездки
    start_stop_drive(driver)

    # Проверка статистики с поллингом
    check_drive_stats_with_retry(driver, max_wait_minutes=12, poll_interval_seconds=30)

    print("\n✅ ТЕСТ УСПЕШНО ЗАВЕРШЁН!")
    print("=" * 50)