# import httpx
# import logging
# from typing import Final
# import os
# import dotenv

# logging.basicConfig(
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
#     level=logging.DEBUG
# )

# api_token: Final = os.environ.get("DIGIKALA_TOKEN")

# async def get_categories(api_token: str) -> list:
#     url = "https://shopapi.ir/api/v1/digikala/category/"
#     headers = {"Authorization": f"Bearer {api_token}"}
#     async with httpx.AsyncClient(
#         timeout=httpx.Timeout(connect=5, read=5, write=5, pool=5)
#     ) as client:
#         try:
#             response = await client.get(url, headers=headers)
#             response.raise_for_status()
#             data = response.json()
#             categories = []
#             for category in data.get("data", {}).get("categories", []):
#                 categories.append({
#                     "name": category.get("title_fa", "N/A"),
#                     "slug": category.get("slug", "")
#                 })
#                 for subcategory in category.get("subcategories", []):
#                     categories.append({
#                         "name": subcategory.get("title_fa", "N/A"),
#                         "slug": subcategory.get("slug", "")
#                     })
#             return categories
#         except httpx.HTTPStatusError as e:
#             logging.error(f"HTTP error fetching categories: {e}")
#             return []
#         except httpx.RequestError as e:
#             logging.error(f"Network error fetching categories: {e}")
#             return []
#         except KeyError as e:
#             logging.error(f"Unexpected response structure: {e}")
#             return []


import httpx
import logging

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG
)

async def get_categories(api_token: str) -> list:
    logging.warning("Category list endpoint not available. Use /deals <category_slug> with known slugs (e.g., mobile, laptop).")
    return []