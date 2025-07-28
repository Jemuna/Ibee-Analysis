from datetime import datetime
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import re

options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
driver = webdriver.Chrome(options=options)

def scrape_product(url):
    driver.get(url)
    driver.implicitly_wait(10)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    data = {
        "Name": "N/A",
        "Price": "N/A",
        "Brand": "N/A",
        "Rating": "N/A",
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "URL": url
    }

    try:
        name_selectors = [
            'h1',  
            '[class*="title"]',
            '[class*="product"]',
            '[id*="title"]',
            '[id*="product"]',
            'span.B_NuCI',  
            '#productTitle' 
        ]
        for selector in name_selectors:
            element = soup.select_one(selector)
            if element and element.text.strip():
                data["Name"] = element.text.strip()
                break

       
        price_selectors = [
            '[class*="price"]',
            '[class*="Price"]',
            '[id*="price"]',
            '[class*="amount"]',
            'div._30jeq3._16Jk6d',  
            '#priceblock_ourprice, #priceblock_dealprice'  
        ]
        for selector in price_selectors:
            element = soup.select_one(selector)
            if element and element.text.strip():
                price_text = re.sub(r'[^\d.,]', '', element.text.strip())
                data["Price"] = price_text
                break

        brand_selectors = [
            '[class*="brand"]',
            '[id*="brand"]',
            '[class*="manufacturer"]',
            'td:contains("Brand") + td',  
            '#bylineInfo'  
        ]
        for selector in brand_selectors:
            element = soup.select_one(selector)
            if element and element.text.strip():
                data["Brand"] = element.text.strip()
                break

        rating_selectors = [
            '[class*="rating"]',
            '[class*="stars"]',
            '[class*="review"]',
            'div._3LWZlK',  
            'span.a-icon-alt'  
        ]
        for selector in rating_selectors:
            element = soup.select_one(selector)
            if element and element.text.strip():
                rating_text = re.search(r'[\d.]+', element.text.strip())
                data["Rating"] = rating_text.group(0) if rating_text else element.text.strip()
                break

    except Exception as e:
        print(f"Error scraping {url}: {str(e)}")

    return data

urls = []
print(" Enter product URLs (type 'done' to finish):")
while True:
    try:
        u = input("Enter URL: ").strip()
        if u.lower() == 'done':
            break
        if u:
            urls.append(u)
    except KeyboardInterrupt:
        print("\nInterrupted.")
        break

all_data = []
for url in urls:
    print(f"Scraping product from {url}...")
    all_data.append(scrape_product(url))

if all_data:
    df = pd.DataFrame(all_data)
    df.to_csv("price_tracker_output.csv", index=False)
    print("Data saved to 'price_tracker_output.csv'")
else:
    print("No valid data to save.")

driver.quit()