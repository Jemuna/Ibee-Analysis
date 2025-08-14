from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import random
import re
from urllib.parse import quote_plus

class ProductScraper:
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None
        
    def setup_driver(self):
        """Setup Chrome driver with optimized options"""
        options = Options()
        
        if self.headless:
            options.add_argument("--headless")
        
        # Performance and stealth options
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Rotate user agents
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        options.add_argument(f"user-agent={random.choice(user_agents)}")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # Execute script to remove webdriver property
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def random_delay(self, min_delay=1, max_delay=3):
        """Add random delay to avoid detection"""
        time.sleep(random.uniform(min_delay, max_delay))
    
    def extract_price(self, price_text):
        """Extract numeric price from text"""
        if not price_text:
            return 0.0
        
        # Remove currency symbols and commas
        price_text = re.sub(r'[₹,\s]', '', price_text)
        
        # Extract numbers including decimals
        price_match = re.search(r'(\d+(?:\.\d+)?)', price_text)
        
        if price_match:
            return float(price_match.group(1))
        return 0.0
    
    def search_amazon(self, product_name, min_price=None, max_price=None):
        """Search Amazon with price filters"""
        self.driver = self.setup_driver()
        results = []
        
        try:
            # Build URL with price filters
            query = quote_plus(product_name)
            url = f"https://www.amazon.in/s?k={query}"
            
            # Add price filters to URL if specified
            if min_price is not None or max_price is not None:
                price_range = ""
                if min_price is not None:
                    price_range += f"{int(min_price * 100)}"
                else:
                    price_range += "0"
                
                price_range += "-"
                
                if max_price is not None:
                    price_range += f"{int(max_price * 100)}"
                else:
                    price_range += "999999900"  # High value for no upper limit
                
                url += f"&rh=p_36:{price_range}"
            
            print(f"Searching Amazon: {url}")
            self.driver.get(url)
            self.random_delay(2, 4)
            
            # Wait for results to load
            wait = WebDriverWait(self.driver, 15)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-component-type='s-search-result']")))
            
            # Multiple selectors for different Amazon layouts
            item_selectors = [
                "div[data-component-type='s-search-result']",
                "div.s-result-item[data-component-type='s-search-result']",
                "div.s-main-slot > div.s-result-item"
            ]
            
            items = []
            for selector in item_selectors:
                items = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if items:
                    break
            
            print(f"Found {len(items)} items on Amazon")
            
            for item in items[:20]:  # Limit to first 20 items
                try:
                    # Product name - multiple selectors
                    name = None
                    name_selectors = [
                        "h2 a span",
                        "h2.a-size-mini span",
                        ".s-size-mini .s-link-style a span",
                        "h2 span"
                    ]
                    
                    for selector in name_selectors:
                        try:
                            name_elem = item.find_element(By.CSS_SELECTOR, selector)
                            name = name_elem.text.strip()
                            if name:
                                break
                        except:
                            continue
                    
                    if not name:
                        continue
                    
                    # Price - multiple selectors
                    price = 0.0
                    price_selectors = [
                        ".a-price-whole",
                        ".a-offscreen",
                        ".a-price .a-offscreen",
                        ".a-price-range .a-offscreen"
                    ]
                    
                    for selector in price_selectors:
                        try:
                            price_elem = item.find_element(By.CSS_SELECTOR, selector)
                            price_text = price_elem.text or price_elem.get_attribute("textContent")
                            price = self.extract_price(price_text)
                            if price > 0:
                                break
                        except:
                            continue
                    
                    # Product link
                    link = None
                    try:
                        link_elem = None
                        try:
                            link_elem = item.find_element(By.CSS_SELECTOR, "h2 a")
                        except:
                            try:
                                link_elem = item.find_element(By.CSS_SELECTOR, "a.a-link-normal")
                            except:
                                pass

                        if link_elem:
                            link_raw = link_elem.get_attribute("href")
                            if link_raw:
                                link_raw = link_raw.strip()
                                if link_raw.startswith("/"):
                                    link = "https://www.amazon.in" + link_raw
                                elif link_raw.startswith("http"):
                                    link = link_raw

                        print(f"Amazon product link: {link}")  # Debug output
                    except Exception as e:
                        print(f"Error getting Amazon link: {e}")

                    
                    # Product image
                    image = None
                    try:
                        img_elem = item.find_element(By.CSS_SELECTOR, "img.s-image")
                        image = img_elem.get_attribute("src")
                    except:
                        try:
                            img_elem = item.find_element(By.CSS_SELECTOR, ".s-product-image-container img")
                            image = img_elem.get_attribute("src")
                        except:
                            pass
                    
                    # Rating (optional)
                    rating = None
                    try:
                        rating_elem = item.find_element(By.CSS_SELECTOR, ".a-icon-alt")
                        rating_text = rating_elem.get_attribute("textContent")
                        rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                        if rating_match:
                            rating = float(rating_match.group(1))
                    except:
                        pass
                    
                    if name and (price > 0 or link):
                        results.append({
                            "name": name,
                            "price": price,
                            "product_url": link or "",
                            "image": image or "",
                            "rating": rating,
                            "source": "Amazon"
                        })
                        
                except Exception as e:
                    print(f"Error processing Amazon item: {e}")
                    continue
        
        except Exception as e:
            print(f"Error searching Amazon: {e}")
        
        finally:
            if self.driver:
                self.driver.quit()
        
        return results
    
    def search_flipkart(self, product_name, min_price=None, max_price=None):
        """Search Flipkart with price filters"""
        self.driver = self.setup_driver()
        results = []
        
        try:
            query = quote_plus(product_name)
            url = f"https://www.flipkart.com/search?q={query}"
            
            # Add price filter params (Flipkart uses p[] in query string)
            price_filter = []
            if min_price is not None:
                price_filter.append(f"min={int(min_price)}")
            if max_price is not None:
                price_filter.append(f"max={int(max_price)}")
            if price_filter:
                url += "&" + "&".join(price_filter)
            
            print(f"Searching Flipkart: {url}")
            self.driver.get(url)

            # Close login popup if it appears
            try:
                WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button._2KpZ6l._2doB4z"))
                ).click()
                print("Closed login popup")
            except:
                pass

            # Wait for product listings
            wait = WebDriverWait(self.driver, 15)
            wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div._1AtVbE")))

            time.sleep(2)  # Ensure all images and prices are loaded

            items = self.driver.find_elements(By.CSS_SELECTOR, "div._1AtVbE")

            print(f"Found {len(items)} Flipkart elements")

            for item in items[:20]:  # Limit to 20 results
                try:
                    # Product Name
                    try:
                        name_elem = item.find_element(By.CSS_SELECTOR, "div._4rR01T")  # Laptop/TV layout
                        name = name_elem.text.strip()
                    except:
                        try:
                            name_elem = item.find_element(By.CSS_SELECTOR, "a.s1Q9rs")  # Mobile layout
                            name = name_elem.text.strip()
                        except:
                            continue
                    
                    # Price
                    price = 0.0
                    try:
                        price_elem = item.find_element(By.CSS_SELECTOR, "div._30jeq3._1_WHN1")
                        price = self.extract_price(price_elem.text)
                    except:
                        pass

                    # Link
                    link = ""
                    try:
                        link_elem = item.find_element(By.TAG_NAME, "a")
                        link_raw = link_elem.get_attribute("href")
                        if link_raw.startswith("/"):
                            link = "https://www.flipkart.com" + link_raw
                        else:
                            link = link_raw
                    except:
                        pass

                    # Image
                    image = ""
                    try:
                        img_elem = item.find_element(By.CSS_SELECTOR, "img._396cs4")
                        image = img_elem.get_attribute("src")
                    except:
                        try:
                            img_elem = item.find_element(By.CSS_SELECTOR, "img._2r_T1I")
                            image = img_elem.get_attribute("src")
                        except:
                            pass

                    # Rating (optional)
                    rating = None
                    try:
                        rating_elem = item.find_element(By.CSS_SELECTOR, "div._3LWZlK")
                        rating = float(rating_elem.text)
                    except:
                        pass

                    if name and (price > 0 or link):
                        results.append({
                            "name": name,
                            "price": price,
                            "product_url": link or "",
                            "image": image or "",
                            "rating": rating,
                            "source": "Flipkart"
                        })

                except Exception as e:
                    print(f"Error processing Flipkart item: {e}")
                    continue

        except Exception as e:
            print(f"Error searching Flipkart: {e}")

        finally:
            if self.driver:
                self.driver.quit()

        return results

    def search_all_platforms(self, product_name, min_price=None, max_price=None, sort_by="price"):
        """Search all platforms and combine results"""
        all_results = []
        
        # Search Amazon
        try:
            amazon_results = self.search_amazon(product_name, min_price, max_price)
            for r in amazon_results:
                if "product_url" not in r and "url" in r:
                    r["product_url"] = r["url"]
            all_results.extend(amazon_results)
            print(f"Amazon returned {len(amazon_results)} results")
        except Exception as e:
            print(f"Error searching Amazon: {e}")
        
        self.random_delay(2, 4)  # Delay between platforms
        
        # Search Flipkart
        try:
            flipkart_results = self.search_flipkart(product_name, min_price, max_price)
            for r in flipkart_results:
                if "product_url" not in r and "url" in r:
                    r["product_url"] = r["url"]
            all_results.extend(flipkart_results)
            print(f"Flipkart returned {len(flipkart_results)} results")
        except Exception as e:
            print(f"Error searching Flipkart: {e}")
        
        # Remove duplicates based on similar names and prices
        unique_results = self.remove_duplicates(all_results)
        
        # Sort results
        if sort_by == "price":
            unique_results.sort(key=lambda x: x["price"])
        elif sort_by == "price_desc":
            unique_results.sort(key=lambda x: x["price"], reverse=True)
        elif sort_by == "rating" and any(r.get("rating") for r in unique_results):
            unique_results.sort(key=lambda x: x.get("rating") or 0, reverse=True)
        
        return unique_results
    
    def remove_duplicates(self, results):
        """Remove duplicate products based on name similarity and price"""
        unique_results = []
        seen = set()
        
        for result in results:
            # Create a simple signature for comparison
            name_words = set(result["name"].lower().split()[:3])  # First 3 words
            price_range = round(result["price"] / 100) * 100  # Round to nearest 100
            signature = (frozenset(name_words), price_range)
            
            if signature not in seen:
                seen.add(signature)
                unique_results.append(result)
        
        return unique_results


# Convenience functions for backward compatibility
def search_amazon(product_name, min_price=None, max_price=None):
    scraper = ProductScraper()
    return scraper.search_amazon(product_name, min_price, max_price)

def search_flipkart(product_name, min_price=None, max_price=None):
    scraper = ProductScraper()
    return scraper.search_flipkart(product_name, min_price, max_price)

def search_all_products(product_name, price_range="all", sort_by="price"):
    """
    Search all platforms with price filtering
    
    Args:
        product_name (str): Product to search for
        price_range (str): Price range like "0-500", "1000-5000", "5000+", or "all"
        sort_by (str): Sort by "price", "price_desc", or "rating"
    
    Returns:
        list: Filtered and sorted product results
    """
    scraper = ProductScraper()
    
    # Parse price range
    min_price, max_price = None, None
    if price_range != "all":
        if "+" in price_range:
            min_price = float(price_range.replace("+", ""))
        elif "-" in price_range:
            price_parts = price_range.split("-")
            min_price = float(price_parts[0])
            max_price = float(price_parts[1])
    
    return scraper.search_all_platforms(product_name, min_price, max_price, sort_by)


if __name__ == "__main__":
    # Example usage
    product = input("Enter product name to search: ")
    price_range = input("Enter price range (e.g., '0-500', '1000+', or 'all'): ").strip() or "all"
    
    print(f"\nSearching for '{product}' with price range '{price_range}'...")
    results = search_all_products(product, price_range)
    
    if not results:
        print("No results found.")
    else:
        print(f"\nFound {len(results)} products:")
        for i, item in enumerate(results[:10], 1):  # Show top 10
            rating_text = f" ({item['rating']}★)" if item.get('rating') else ""
            print(f"{i}. [{item['source']}] {item['name']}{rating_text}")
            print(f"   Price: ₹{item['price']}")
            if item['product_url']:
                print(f"   URL: {item['product_url']}")
            print() 







            