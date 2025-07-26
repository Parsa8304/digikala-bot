import httpx
import logging
import asyncio
from typing import Final
import dotenv
import os


dotenv.load_dotenv()

api_token: Final = os.environ.get('DIGIKALA_TOKEN')


# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG
)

import httpx
import logging
import asyncio

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG
)

async def get_discounted_products(api_token: str, category_slug: str, page: int = 1, limit: int = 10) -> list:
    url = f"http://shopapi.ir/api/v1/digikala/category/products/{category_slug}?page={page}"
    headers = {"Authorization": f"Bearer {api_token}"}
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(connect=5, read=5, write=5, pool=5),
        follow_redirects=True
    ) as client:
        try:
            logging.debug(f"Requesting products from {url}")
            response = await client.get(url, headers=headers)
            logging.debug(f"Response status: {response.status_code}")
            logging.debug(f"Response body: {response.text}")
            response.raise_for_status()
            data = response.json()
            discounted_products = []
            for product in data.get("data", {}).get("products", []):
                discount = product.get("attributes", {}).get("discount_percent", 0)
                if discount > 0:
                    discounted_products.append({
                        "title": product.get("attributes", {}).get("title_fa", "N/A"),
                        "price": product.get("attributes", {}).get("discounted_price", 0) / 10_000,  # IRR
                        "discount_percent": discount,
                        "product_id": product.get("attributes", {}).get("id", ""),
                        "url": product.get("attributes", {}).get("url", "")
                    })
                if len(discounted_products) >= limit:
                    break
            logging.debug(f"Parsed {len(discounted_products)} discounted products")
            return discounted_products
        except httpx.HTTPStatusError as e:
            logging.error(f"HTTP error fetching products for category {category_slug}: {e}")
            return []
        except httpx.RequestError as e:
            logging.error(f"Network error fetching products for category {category_slug}: {e}")
            return []
        except ValueError as e:
            logging.error(f"JSON decode error for category {category_slug}: {e}")
            return []
        except KeyError as e:
            logging.error(f"Unexpected response structure for category {category_slug}: {e}")
            return []

async def get_product_by_dkp(api_token: str, dkp: str) -> dict:
    url = f"https://shopapi.ir/api/v1/digikala/products/{dkp}"
    headers = {"Authorization": f"Bearer {api_token}"}
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(connect=5, read=5, write=5, pool=5),
        follow_redirects=True
    ) as client:
        try:
            logging.debug(f"Requesting product from {url}")
            response = await client.get(url, headers=headers)
            logging.debug(f"Response status: {response.status_code}")
            logging.debug(f"Response body: {response.text}")
            response.raise_for_status()
            data = response.json()
            product = data.get("data", {}).get("attributes", {})
            return {
                "title": product.get("title_fa", "N/A"),
                "price": product.get("discounted_price", 0) / 10_000,
                "main_price": product.get("main_price", 0) / 10_000,
                "url": product.get("url", ""),
                "image": product.get("featured_image", [""])[0]
            }
        except httpx.HTTPStatusError as e:
            logging.error(f"HTTP error fetching product {dkp}: {e}")
            return {}
        except httpx.RequestError as e:
            logging.error(f"Network error fetching product {dkp}: {e}")
            return {}
        except ValueError as e:
            logging.error(f"JSON decode error for product {dkp}: {e}")
            return {}
        except KeyError as e:
            logging.error(f"Unexpected response structure for product {dkp}: {e}")
            return {}