import os
import time
import random
import tempfile
from multiprocessing import Pool
from typing import List

from fastapi import UploadFile
from selenium.common import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

SCROLL_PAUSE_TIME = 5
PROCESS_COUNT = 3

USERNAMES = os.getenv('USERNAMES')
PASSWORDS = os.getenv('USERNAME_PASSWORDS')

USERNAMES = USERNAMES.split(" ") if USERNAMES else []
PASSWORDS = PASSWORDS.split(" ") if PASSWORDS else []


def check__element_exists(driver, by, element):
    try:
        driver.find_element(by, element)
    except NoSuchElementException:
        return False
    return True


def log_into_instagram(driver, user_creds):
    driver.get("https://www.instagram.com/")
    driver.implicitly_wait(random.randrange(15, 20))
    if check__element_exists(driver, By.XPATH, "//button[text()='Decline optional cookies']"):
        decline_cookies_btn = driver.find_element(By.XPATH, "//button[text()='Decline optional cookies']")
        decline_cookies_btn.click()

    driver.implicitly_wait(20)
    username_field = driver.find_element(By.NAME, 'username')
    username_field.send_keys(user_creds['username'])

    password_field = driver.find_element(By.NAME, 'password')
    password_field.send_keys(user_creds['password'])

    login_btn = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
    login_btn.click()
    driver.implicitly_wait(20)
    time.sleep(20)


def get_chrome_driver():
    chrome_options = Options()
    chrome_options.page_load_strategy = 'normal'
    chrome_options.add_argument("--headless")
    return webdriver.Chrome(options=chrome_options, service=ChromeService(ChromeDriverManager().install()))


def get_instagram_photos(user_creds: dict, username_to_search: str, max_count: int):
    driver = get_chrome_driver()

    try:
        log_into_instagram(driver, user_creds)

        driver.get(f"https://www.instagram.com/{username_to_search}/")

        time.sleep(20)
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(SCROLL_PAUSE_TIME)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        driver.implicitly_wait(20)
        time.sleep(20)

        images = driver.find_elements(By.XPATH, '//article//img')
        image_urls = [img.get_attribute("src") for img in images]
        image_urls = [url for url in image_urls if 'scontent' in url and 'profile' not in url]
        num_images = min(max_count, len(image_urls))

        return image_urls[:num_images]
    finally:
        driver.quit()


def post_photos_to_profile(user_creds: dict, photos: List[UploadFile], caption: str):
    driver = get_chrome_driver()

    try:
        log_into_instagram(driver, user_creds)

        driver.implicitly_wait(15)
        new_post_btn = driver.find_element(By.CSS_SELECTOR, "[aria-label='New post']")

        time.sleep(15)
        if check__element_exists(driver, By.XPATH, "//button[text()='Decline optional cookies']"):
            decline_cookies_btn = driver.find_element(By.XPATH, "//button[text()='Decline optional cookies']")
            decline_cookies_btn.click()

        new_post_btn.click()

        for photo in photos:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{photo.filename.split(".")[-1]}') as tmp:
                tmp.write(photo.file.read())
                tmp_path = tmp.name

            photo_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
            )
            photo_input.send_keys(os.path.abspath(tmp_path))

            os.remove(tmp_path)

        next_btn = driver.find_element(By.XPATH, "//button[text()='Next']")
        next_btn.click()

        driver.implicitly_wait(15)
        caption_input = driver.find_element(By.XPATH, "//textarea[@aria-label='Write a caption…']")
        caption_input.send_keys(caption)

        publish_btn = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Share')]"))
        )
        publish_btn.click()
        post_url_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/p/')]"))
        )
        post_url = post_url_element.get_attribute("href")

        return post_url
    finally:
        driver.quit()


def apply_function_in_parallel(func, *args):
    pool = Pool(processes=PROCESS_COUNT)
    tasks = list()
    for i in range(len(USERNAMES)):
        user_creds = {'username': USERNAMES[i], 'password': PASSWORDS[i]}
        tasks.append(pool.apply_async(func, (user_creds,)+args))

    result = []
    for task in tasks:
        result.extend(task.get())

    return result
