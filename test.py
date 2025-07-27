import httpx
import asyncio
import os
import dotenv
import logging
from typing import Final


dotenv.load_dotenv()



URLS = [
    "https://shopapi.ir/api/v1/digikala/category/products/mobile/",
    "https://shopapi.ir/api/v1/digikala/category/products/electronic-devices",
    "https://shopapi.ir/api/v1/digikala/category/products/home-and-kitchen/",
    
    ]

token: Final = os.environ.get("DIGIKALA_TOKEN")



async def fetch_categories(url: str, token: str) -> list:
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(timeout=httpx.Timeout(connect=5, read=5, write=5, pool=5)) as client:
        try:
            response = await client.get(url, headers=headers)
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
            return categories
        except httpx.HTTPStatusError as e:
            logging.error(f"HTTP error occurred: {e}")
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            
            
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    if not token:
        logging.error("DIGIKALA_TOKEN environment variable not set.")
        exit(1)
    
    async def main():
        tasks = [fetch_categories(url, token) for url in URLS]
        results = await asyncio.gather(*tasks)
        all_categories = [cat for sublist in results for cat in sublist]
        logging.info(f"Retrieved {len(all_categories)} categories from all URLs.")
    
    asyncio.run(main())
    logging.info("Script completed successfully.")