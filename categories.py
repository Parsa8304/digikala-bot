
#TODO: refactor the endpoint and it's logic to use in the main.py

import httpx
import logging
from typing import Final
import os
import dotenv
import asyncio
dotenv.load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG
)

api_token: Final = os.environ.get("DIGIKALA_TOKEN")

async def get_categories(api_token: str) -> list:
    url = "https://shopapi.ir/api/v1/digikala/category/products/mobile/"
    headers = {"Authorization": f"Bearer {api_token}"}
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(connect=5, read=5, write=5, pool=5)
    ) as client:
        try:
            response = await client.get(url, headers=headers)
            logging.debug(f"ShopAPI response: status={response.status_code}, content={response.text}")
            response.raise_for_status()
            data = response.json()
            categories = []
            for category in data.get("data", {}).get("categories", []):
                categories.append({
                    "name": category.get("title_fa", "N/A"),
                    "slug": category.get("slug", "")
                })
                for subcategory in category.get("subcategories", []):
                    categories.append({
                        "name": subcategory.get("title_fa", "N/A"),
                        "slug": subcategory.get("slug", "")
                    })
            if not categories:
                logging.warning("No categories found in response")
            return categories
        except httpx.HTTPStatusError as e:
            logging.error(f"HTTP error fetching categories: status={e.response.status_code}, content={e.response.text}")
            return []
        except httpx.RequestError as e:
            logging.error(f"Network error fetching categories: {e}")
            return []
        except KeyError as e:
            logging.error(f"Unexpected response structure: {e}, response={response.text}")
            return []
        except Exception as e:
            logging.error(f"Unexpected error fetching categories: {e}")
            return []

async def test_get_categories():
    if not api_token:
        logging.error("DIGIKALA_TOKEN environment variable not set.")
        return
    logging.info("Testing get_categories function...")
    categories = await get_categories(api_token)
    if categories:
        logging.info(f"Retrieved {len(categories)} categories:")
        for cat in categories[:5]:  # Print first 5 for brevity
            logging.info(f"- Name: {cat['name']}, Slug: {cat['slug']}")
    else:
        logging.warning("No categories retrieved. Check API token, endpoint, or credits.")

if __name__ == "__main__":
    asyncio.run(test_get_categories())