import re
from decimal import Decimal
from .models import Product
import requests
from bs4 import BeautifulSoup


URL_SCRAPING_DOMAIN = 'https://www.stroysa.tomsk.ru'
URL_SCRAPING = 'https://www.stroysa.tomsk.ru/catalog/profilnye_truby_ugolki/'


class ScrapingError(Exception):
    pass


class ScrapingTimeoutError(ScrapingError):
    pass


class ScrapingHTTPError(ScrapingError):
    pass


class ScrapingOtherError(ScrapingError):
    pass


def scraping():
    try:
        resp = requests.get(URL_SCRAPING, timeout=10.0)
    except requests.exceptions.Timeout:
        raise ScrapingTimeoutError("request timed out")
    except Exception as e:
        raise ScrapingOtherError(f'{e}')

    if resp.status_code != 200:
        raise ScrapingHTTPError(f"HTTP {resp.status_code}: {resp.text}")

    data_list = []
    html = resp.text
    soup = BeautifulSoup(html, 'html.parser')
    blocks = soup.select('.catalog-item-card ')
    for block in blocks:
        data = {}
        name = block.select_one('.item-title[title]').get_text().strip()
        data['name'] = name

        image_url = URL_SCRAPING_DOMAIN + block.select_one('img')['src']
        data['image_url'] = image_url

        price_raw = block.select_one('.item-price ').text
        # '\r\n \t\t\t\t\t\t\t\t\t\t\t\t\t\t493.00\t\t\t\t\t\t\t\t\t\t\t\t  руб. '
        price = re.findall(r'\S\d+\.\d+\S', price_raw)[0]
        price = Decimal(price)
        data['price'] = price  # 493.00

        unit = block.select_one('.unit ').text.strip()
        # '\r\n \t\t\t\t\t\t\t\t\t\t\t\t\t\tза шт\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t'
        data['unit'] = unit  # 'за шт'
        # find and open detail page
        url_detail = block.select_one('.item-title')
        # <a class="item-title" href="/catalog/profilnye_truby_ugolki/truba_profilnaya_40kh20_2_mm_3m/" itemprop="url" title="Труба профильная 40х20 2 мм 3м">

        url_detail = url_detail['href']
        # '/catalog/profilnye_truby_ugolki/truba_profilnaya_40kh20_2_mm_3m/'

        url_detail = URL_SCRAPING_DOMAIN + url_detail

        html_detail = requests.get(url_detail).text
        soup = BeautifulSoup(html_detail, 'html.parser')
        code_block = soup.select_one('.catalog-detail-property')
        code = code_block.select_one('b').text
        data['code'] = code

        data_list.append(data)

        print(data)

        for item in data_list:
            if not Product.objects.filter(code=item['code']).exists():
                Product.objects.create(
                    name=item['name'],
                    code=item['code'],
                    price=item['price'],
                    unit=item['unit'],
                    image_url=item['image_url'],
                )

    return data_list


if __name__ == '__main__':
    scraping()
