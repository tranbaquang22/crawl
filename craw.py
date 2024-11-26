from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import csv
import time


# Cấu hình các tùy chọn Chrome
options = Options()
options.add_argument('--headless')  # Chạy ở chế độ không hiển thị
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--window-size=1920,1080')
options.add_argument('--disable-software-rasterizer')
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36"
)

# Sử dụng webdriver_manager để tự động tải chromedriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

base_url = 'https://soufeel.com/collections/all'


def get_html(url):
    """Lấy nội dung HTML từ URL."""
    try:
        print(f"Đang truy cập URL: {url}")
        driver.get(url)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "product-item-list"))
        )
        time.sleep(2)
        return driver.page_source
    except Exception as e:
        print(f"Đã xảy ra lỗi khi truy cập URL: {url}")
        print(e)
        return None


def parse_products(html):
    """Phân tích danh sách sản phẩm từ trang chính."""
    soup = BeautifulSoup(html, 'html.parser')
    products = []
    product_list = soup.find_all('div', class_='product-item-list')
    for product in product_list:
        try:
            name = product.find('div', class_='product-card__name').get_text(strip=True)
            link = product.find('a', class_='product-card')['href']
            if not link.startswith('http'):
                link = 'https://soufeel.com' + link
            image = product.find('img', class_='defaultImage')['src']
            if image.startswith('//'):
                image = 'https:' + image
            products.append({'Name': name, 'Link': link, 'Image': image})
        except AttributeError:
            continue
    return products


def parse_product_details(link):
    """Lấy thông tin chi tiết của sản phẩm từ trang chi tiết."""
    try:
        driver.get(link)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "ProductInfo-main-product-info"))
        )
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Lấy giá
        sale_price = soup.find('span', id='ProductPriceproduct-page-price')
        sale_price = sale_price.get_text(strip=True) if sale_price else "N/A"

        original_price = soup.find('span', id='ProductComparePriceproduct-page-price')
        original_price = original_price.get_text(strip=True) if original_price else "N/A"

        discount = soup.find('span', id='ProductDiscountPriceproduct-page-price')
        discount = discount.get_text(strip=True) if discount else "N/A"

        # Lấy mô tả và chi tiết
        description = soup.find('div', id='description_tab')
        description = description.get_text(strip=True) if description else "N/A"

        product_details = soup.find('div', id='details_tab')
        product_details = product_details.get_text(strip=True) if product_details else "N/A"

        return {
            'Sale Price': sale_price,
            'Original Price': original_price,
            'Discount': discount,
            'Description': description,
            'Product Details': product_details
        }
    except Exception as e:
        print(f"Lỗi khi lấy thông tin chi tiết từ link: {link}")
        print(e)
        return {
            'Sale Price': "N/A",
            'Original Price': "N/A",
            'Discount': "N/A",
            'Description': "N/A",
            'Product Details': "N/A"
        }


def save_to_csv(products, filename='products.csv'):
    """Lưu danh sách sản phẩm vào file CSV."""
    if not products:
        print("Không có sản phẩm nào để lưu.")
        return
    keys = products[0].keys()
    with open(filename, 'w', newline='', encoding='utf-8') as output_file:
        dict_writer = csv.DictWriter(output_file, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(products)


def main():
    all_products = []
    page = 1
    desired_count = 500  # Số lượng sản phẩm cần thu thập

    while len(all_products) < desired_count:
        url = f"{base_url}?page={page}"
        print(f"Lấy dữ liệu từ trang: {url}")
        html = get_html(url)
        if not html:
            break

        # Parse danh sách sản phẩm từ trang chính
        products = parse_products(html)
        if not products:
            print("Không còn sản phẩm để thu thập.")
            break

        # Với mỗi sản phẩm, mở trang chi tiết để lấy thêm thông tin
        for product in products:
            details = parse_product_details(product['Link'])
            product.update(details)

        all_products.extend(products)
        print(f"Đã thu thập được {len(all_products)} sản phẩm.")
        page += 1

    # Giới hạn số lượng sản phẩm nếu vượt quá yêu cầu
    all_products = all_products[:desired_count]

    if all_products:
        save_to_csv(all_products)
        print(f"Đã lưu {len(all_products)} sản phẩm vào file products.csv.")
    else:
        print("Không có sản phẩm nào được thu thập.")

    driver.quit()


if __name__ == "__main__":
    main()
