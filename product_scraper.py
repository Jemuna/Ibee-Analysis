# product_scraper.py

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import csv
from datetime import datetime
import re
import time

def get_amazon_data(url, threshold):
    try:
        # Set up headless Chrome browser
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--window-size=1920x1080')

        driver = webdriver.Chrome(options=options)
        driver.get(url)
        time.sleep(3)  

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        name = soup.select_one('#productTitle')
        price = soup.select_one('span.a-price > span.a-offscreen')
        brand = soup.select_one('#bylineInfo')
        rating = soup.select_one('span.a-icon-alt')

        driver.quit()

        return {
            'site': 'Amazon',
            'name': name.get_text(strip=True) if name else 'N/A',
            'price': float(re.sub(r'[^\d.]', '', price.text)) if price else 0.0,
            'brand': brand.get_text(strip=True) if brand else 'N/A',
            'rating': rating.get_text(strip=True).split()[0] if rating else 'N/A',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'url': url,
            'threshold': threshold
        }

    except Exception as e:
        print(f"Amazon Scraping Error: {e}")
        return None

# Add the div and class selectors for Flipkart, Meesho, Croma, Shopsy, and Reliance Digital as per the latest website structure as they may change over time.   

def get_flipkart_data(url, threshold):
    try:
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--window-size=1920x1080')

        driver = webdriver.Chrome(options=options)
        driver.get(url)
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        name = soup.select_one('span.B_NuCI') or soup.select_one('span.VU-ZEz')
        price = soup.select_one('div._30jeq3._16Jk6d') or soup.select_one('div.Nx9bqj.CxhGGd')
        brand = soup.select_one('a._2whKao')  
        rating = soup.select_one('div._3LWZlK') or soup.select_one('div.XQDdHH')


        driver.quit()

        return {
            'site': 'Flipkart',
            'name': name.get_text(strip=True) if name else 'N/A',
            'price': float(re.sub(r'[^\d.]', '', price.text)) if price else 0.0,
            'brand': brand.get_text(strip=True) if brand else 'N/A',
            'rating': rating.get_text(strip=True) if rating else 'N/A',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'url': url,
            'threshold': threshold
        }

    except Exception as e:
        print(f"Flipkart Scraping Error: {e}")
        return None



def get_meesho_data(url, threshold):
    try:
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--window-size=1920x1080')

        driver = webdriver.Chrome(options=options)
        driver.get(url)
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        name = soup.select_one('h1.ProductDetails__title')
        price = soup.select_one('span.ProductDetails__price-value')
        brand = soup.select_one('div.ProductDetails__brand-name')
        rating = soup.select_one('div.Ratings__rating')

        driver.quit()

        return {
            'site': 'Meesho',
            'name': name.get_text(strip=True) if name else 'N/A',
            'price': float(re.sub(r'[^\d.]', '', price.text)) if price else 0.0,
            'brand': brand.get_text(strip=True) if brand else 'N/A',
            'rating': rating.get_text(strip=True) if rating else 'N/A',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'url': url,
            'threshold': threshold
        }

    except Exception as e:
        print(f"Meesho Scraping Error: {e}")
        return None


def get_croma_data(url, threshold):
    try:
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--window-size=1920x1080')

        driver = webdriver.Chrome(options=options)
        driver.get(url)
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        name = soup.select_one('h1.pdp-title')
        price = soup.select_one('span.amount')
        brand = soup.select_one('div.product-brand > a')
        rating = soup.select_one('span.bv_avgRating_component_container')

        driver.quit()

        return {
            'site': 'Croma',
            'name': name.get_text(strip=True) if name else 'N/A',
            'price': float(re.sub(r'[^\d.]', '', price.text)) if price else 0.0,
            'brand': brand.get_text(strip=True) if brand else 'N/A',
            'rating': rating.get_text(strip=True) if rating else 'N/A',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'url': url,
            'threshold': threshold
        }

    except Exception as e:
        print(f"Croma Scraping Error: {e}")
        return None

def get_shopsy_data(url, threshold):
    try:
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--window-size=1920x1080')

        driver = webdriver.Chrome(options=options)
        driver.get(url)
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        name = soup.select_one('span._2BULo')  
        price = soup.select_one('div._30jeq3') 
        brand = soup.select_one('span.G6XhRU')  
        rating = soup.select_one('div._3LWZlK')  

        driver.quit()

        return {
            'site': 'Shopsy',
            'name': name.get_text(strip=True) if name else 'N/A',
            'price': float(re.sub(r'[^\d.]', '', price.text)) if price else 0.0,
            'brand': brand.get_text(strip=True) if brand else 'N/A',
            'rating': rating.get_text(strip=True) if rating else 'N/A',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'url': url,
            'threshold': threshold
        }

    except Exception as e:
        print(f"Shopsy Scraping Error: {e}")
        return None

def get_reliance_data(url, threshold):
    try:
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--window-size=1920x1080')

        driver = webdriver.Chrome(options=options)
        driver.get(url)
        time.sleep(4)

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        name = soup.select_one('h1.pdp__title')
        price = soup.select_one('span.pdp__offerPrice') or soup.select_one('span.pdp__price')
        brand = soup.select_one('div.pdp__brand-name')
        rating = soup.select_one('div.ReviewModule__reviewScore')  

        driver.quit()

        return {
            'site': 'Reliance Digital',
            'name': name.get_text(strip=True) if name else 'N/A',
            'price': float(re.sub(r'[^\d.]', '', price.text)) if price else 0.0,
            'brand': brand.get_text(strip=True) if brand else 'N/A',
            'rating': rating.get_text(strip=True) if rating else 'N/A',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'url': url,
            'threshold': threshold
        }

    except Exception as e:
        print(f"Reliance Digital Scraping Error: {e}")
        return None



def save_to_csv(data, file='price_data.csv'):
    header = ['timestamp', 'site', 'name', 'price', 'brand', 'rating', 'url', 'threshold']
    try:
        with open(file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=header)
            if f.tell() == 0:
                writer.writeheader()
            writer.writerow(data)
    except Exception as e:
        print(f"CSV Save Error: {e}")

def track_product(url, threshold):
    if "amazon" in url:
        data = get_amazon_data(url, threshold)
    elif "flipkart" in url:
        data = get_flipkart_data(url, threshold)
    elif "meesho" in url:
        data = get_meesho_data(url, threshold)
    elif "croma" in url:
        data = get_croma_data(url, threshold)
    elif "shopsy" in url:
        data = get_shopsy_data(url, threshold)
    elif "reliancedigital" in url:
        data = get_reliance_data(url, threshold)
    else:
        print("Only Amazon scraping is supported currently.")
        return

    if data:
        save_to_csv(data)
        print(" Product data saved to CSV.")
        if data['price'] < threshold:
            print(f" Deal Alert! '{data['name']}' is now ₹{data['price']} (Below ₹{threshold})")
    else:
        print("Failed to scrape the product.")


if __name__ == "__main__":
    url = input("Enter Amazon product URL: ")
    threshold = float(input("Enter threshold price: "))
    track_product(url, threshold)
