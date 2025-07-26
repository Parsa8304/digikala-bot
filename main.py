import logging
import asyncio
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.request import HTTPXRequest
from categories import get_categories
from products import get_discounted_products, get_product_by_dkp
from typing import Final
import dotenv

dotenv.load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG
)

SHOPAPI_TOKEN: Final = os.environ.get("DIGIKALA_TOKEN")
TELEGRAM_TOKEN: Final = os.environ.get("TELEGRAM_TOKEN")
BOT_USERNAME: Final = os.environ.get("BOT_USERNAME")

async def categories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not SHOPAPI_TOKEN:
        await update.message.reply_text("Error: ShopAPI token not configured.")
        return
    logging.debug("Fetching categories from shopapi.ir")
    categories_list = await get_categories(SHOPAPI_TOKEN)
    if categories_list:
        response = "\n".join([f"{cat['name']} ({cat['slug']})" for cat in categories_list[:20]])
        await update.message.reply_text(f"Available categories:\n{response}\nUse /deals <category_slug> to see discounted products.")
    else:
        await update.message.reply_text("Category list unavailable. Use /deals <category_slug> (e.g., /deals mobile, /deals laptop) or /product <dkp> (e.g., /product 9887451).")

async def deals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not SHOPAPI_TOKEN:
        await update.message.reply_text("Error: ShopAPI token not configured.")
        return
    if not context.args:
        await update.message.reply_text("Please provide a category slug (e.g., /deals mobile)")
        return
    category_slug = context.args[0]
    logging.debug(f"Fetching products for category: {category_slug}")
    discounted_products = await get_discounted_products(SHOPAPI_TOKEN, category_slug, limit=5)
    if discounted_products:
        response = "\n".join([
            f"{p['title']}: {p['price']} IRR ({p['discount_percent']}% off)\nLink: {p['url']}"
            for p in discounted_products
        ])
        await update.message.reply_text(f"Discounted products in {category_slug}:\n{response}")
    else:
        await update.message.reply_text(
            f"No discounted products found in {category_slug}. This may be due to insufficient API credits or an invalid category. Try /deals mobile or /product 9887451."
        )

async def product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not SHOPAPI_TOKEN:
        await update.message.reply_text("Error: ShopAPI token not configured.")
        return
    if not context.args:
        await update.message.reply_text("Please provide a product DKP (e.g., /product 9887451)")
        return
    dkp = context.args[0]
    logging.debug(f"Fetching product with DKP: {dkp}")
    product_data = await get_product_by_dkp(SHOPAPI_TOKEN, dkp)
    if product_data:
        response = (
            f"{product_data['title']}:\n"
            f"Price: {product_data['price']} IRR\n"
            f"Main Price: {product_data['main_price']} IRR\n"
            f"Link: {product_data['url']}\n"
            f"Image: {product_data['image']}"
        )
        await update.message.reply_text(response)
    else:
        await update.message.reply_text(
            f"Product with DKP {dkp} not found. This may be due to insufficient API credits or an invalid DKP. Try /product 9887451."
        )

async def main():
    if not TELEGRAM_TOKEN:
        logging.error("TELEGRAM_TOKEN environment variable not set.")
        return
    if not SHOPAPI_TOKEN:
        logging.error("DIGIKALA_TOKEN environment variable not set.")
        return
    request = HTTPXRequest(connect_timeout=5, read_timeout=5)
    logging.debug("Building Telegram application")
    app = Application.builder().token(TELEGRAM_TOKEN).request(request).build()
    app.add_handler(CommandHandler("categories", categories))
    app.add_handler(CommandHandler("deals", deals))
    app.add_handler(CommandHandler("product", product))
    try:
        logging.debug("Initializing application")
        await app.initialize()
        logging.debug("Starting polling")
        await app.run_polling(
            poll_interval=3,
            drop_pending_updates=True,
            bootstrap_retries=5,
            timeout=20
        )
    except KeyboardInterrupt:
        logging.info("Received KeyboardInterrupt, shutting down gracefully...")
    except Exception as e:
        logging.error(f"Failed to run bot: {e}", exc_info=True)
    finally:
        logging.debug("Stopping application")
        await app.stop()
        logging.debug("Shutting down application")
        await app.shutdown()

if __name__ == "__main__":
    asyncio.run(main())