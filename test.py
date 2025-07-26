import httpx
import asyncio
import os
import dotenv

dotenv.load_dotenv()

async def test_endpoint(url):
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {os.environ.get('DIGIKALA_TOKEN')}"}
            )
            print(f"\nEndpoint: {url}")
            print(f"Status: {response.status_code}")
            print(f"Headers: {response.headers}")
            print(f"Body: {response.text}")
        except httpx.RequestError as e:
            print(f"\nEndpoint: {url}")
            print(f"Network error: {e}")

async def test_all():
    endpoints = [
        "https://shopapi.ir/api/v1/digikala/products/9887451",
        "http://shopapi.ir/api/v1/digikala/category/products/mobile",
        "http://shopapi.ir/api/v1/digikala/category/products/notebook-netbook-ultrabook"
    ]
    for url in endpoints:
        await test_endpoint(url)

asyncio.run(test_all())