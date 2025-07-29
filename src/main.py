import logging
import asyncio
import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    ConversationHandler,
)
from telegram.request import HTTPXRequest
from src.categories import get_category
from src.products import get_discounted_products, get_product_by_dkp
from typing import Final, List, Dict
import dotenv
import aiohttp

dotenv.load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG
)

SHOPAPI_TOKEN: Final = os.environ.get("DIGIKALA_TOKEN")
# SHOPAPI_TOKEN: Final = "RHDMsIicI5RuGMkqcv06qHWXa7wUA910OqQvJezx"

TELEGRAM_TOKEN: Final = os.environ.get("TELEGRAM_TOKEN")
BOT_USERNAME: Final = os.environ.get("BOT_USERNAME")
DIGIKALA_API_BASE_URL: Final = "https://shopapi.ir/api/v1/digikala/category/products"

# Log token presence (partially masked for security)
if SHOPAPI_TOKEN:
    logging.info(f"DIGIKALA_TOKEN loaded: {SHOPAPI_TOKEN[:4]}...{SHOPAPI_TOKEN[-4:]}")
else:
    logging.error("DIGIKALA_TOKEN is not set in environment variables.")

# Static categories (12, including confirmed 'mobile')
CATEGORIES: Final = [
    {"id": "1", "name": "موبایل", "slug": "mobile"},
    {"id": "2", "name": "خانه و آشپزخانه", "slug": "home-and-kitchen"},
    {"id": "3", "name": "پوشاک", "slug": "apparel"},
    {"id": "4", "name": "مواد غذایی", "slug": "food-beverage"},
    {"id": "5", "name": "کتاب و رسانه", "slug": "book-and-media"},
    {"id": "6", "name": "مادر و کودک", "slug": "mother-and-child"},
    {"id": "7", "name": "لوازم شخصی", "slug": "personal-appliance"},
    {"id": "8", "name": "ورزش و سرگرمی", "slug": "sport-entertainment"},
    {"id": "9", "name": "قطعات خودرو", "slug": "vehicles-spare-parts"},
    {"id": "10", "name": "محصولات روستایی", "slug": "rural-products"},
    {"id": "11", "name": "کارت هدیه", "slug": "dk-ds-gift-cards"},
    {"id": "12", "name": "سایر", "slug": "other"},
]


# async def get_products_by_category(category_slug: str) -> List[Dict]:
#     if not SHOPAPI_TOKEN:
#         logging.error("DIGIKALA_TOKEN is not set, cannot fetch products.")
#         return []
#     async with aiohttp.ClientSession() as session:
#         url = f"{DIGIKALA_API_BASE_URL}/{category_slug}"
#         headers = {"Authorization": f"Bearer {SHOPAPI_TOKEN}"}
#         logging.debug(f"Making API request to {url} with headers: Authorization: Bearer {SHOPAPI_TOKEN[:4]}...{SHOPAPI_TOKEN[-4:]}")
#         try:
#             async with session.get(url, headers=headers) as response:
#                 logging.debug(f"API response status: {response.status}")
#                 logging.debug(f"API response headers: {response.headers}")
#                 if response.status == 200:
#                     data = await response.json()
#                     logging.debug(f"API response data: {data}")
#                     products = []
#                     for item in data.get("data", []):
#                         if item.get("type") == "products":
#                             attr = item.get("attributes", {})
#                             dkp_match = re.search(r"dkp-(\d+)", attr.get("url", ""))
#                             dkp = dkp_match.group(1) if dkp_match else None
#                             main_price = attr.get("main_price", 0)
#                             discounted_price = attr.get("discounted_price", 0)
#                             if dkp and discounted_price > 0 and discounted_price < main_price:
#                                 products.append({
#                                     "id": dkp,
#                                     "title_fa": attr.get("title_fa", ""),
#                                     "main_price": main_price,
#                                     "discounted_price": discounted_price,
#                                     "url": attr.get("url", ""),
#                                     "featured_image": attr.get("featured_image", [None])[0]
#                                 })
#                             elif not dkp:
#                                 logging.warning(f"No DKP found for product: {attr.get('title_fa', 'Unknown')}")
#                             elif discounted_price >= main_price or discounted_price == 0:
#                                 logging.info(f"Product not discounted: {attr.get('title_fa', 'Unknown')} (Main: {main_price}, Discounted: {discounted_price})")
#                     logging.debug(f"Filtered {len(products)} discounted products for category {category_slug}")
#                     return products
#                 elif response.status == 401:
#                     logging.error(f"Authentication failed for {url}: {await response.text()}")
#                     return []
#                 else:
#                     logging.error(f"API request failed with status {response.status}: {await response.text()}")
#                     return []
#         except Exception as e:
#             logging.error(f"Error fetching products for {category_slug}: {e}")
#             return []

# New function: returns all products regardless of discount
async def get_all_products_by_category(category_slug: str) -> List[Dict]:
    if not SHOPAPI_TOKEN:
        logging.error("DIGIKALA_TOKEN is not set, cannot fetch products.")
        return []
    async with aiohttp.ClientSession() as session:
        url = f"{DIGIKALA_API_BASE_URL}/{category_slug}"
        headers = {"Authorization": f"Bearer {SHOPAPI_TOKEN}"}
        logging.debug(f"Making API request to {url} with headers: Authorization: Bearer {SHOPAPI_TOKEN[:4]}...{SHOPAPI_TOKEN[-4:]}")
        try:
            async with session.get(url, headers=headers) as response:
                logging.debug(f"API response status: {response.status}")
                logging.debug(f"API response headers: {response.headers}")
                if response.status == 200:
                    data = await response.json()
                    logging.debug(f"API response data: {data}")
                    products = []
                    for item in data.get("data", []):
                        if item.get("type") == "products":
                            attr = item.get("attributes", {})
                            dkp_match = re.search(r"dkp-(\d+)", attr.get("url", ""))
                            dkp = dkp_match.group(1) if dkp_match else None
                            products.append({
                                "id": dkp,
                                "title_fa": attr.get("title_fa", ""),
                                "main_price": attr.get("main_price", 0),
                                "discounted_price": attr.get("discounted_price", 0),
                                "url": attr.get("url", ""),
                                "featured_image": attr.get("featured_image", [None])[0]
                            })
                    logging.debug(f"Returned {len(products)} products for category {category_slug}")
                    return products
                elif response.status == 401:
                    logging.error(f"Authentication failed for {url}: {await response.text()}")
                    return []
                else:
                    logging.error(f"API request failed with status {response.status}: {await response.text()}")
                    return []
        except Exception as e:
            logging.error(f"Error fetching products for {category_slug}: {e}")
            return []

# Conversation states
CATEGORY, PRODUCTS = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send a welcome message with category buttons."""
    keyboard = [
        [InlineKeyboardButton(cat["name"], callback_data=f"category_{cat['slug']}")]
        for cat in CATEGORIES
    ]
    keyboard.append([
        InlineKeyboardButton("Deals", callback_data="deals"),
        InlineKeyboardButton("Product", callback_data="product"),
        InlineKeyboardButton("Help", callback_data="help"),
    ])
    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_message = (
        f"Welcome to {BOT_USERNAME}!\n"
        "Choose a category to view discounted products or use the command buttons below:\n"
        "- Deals: View discounted products (e.g., /deals mobile)\n"
        "- Product: Get details for a product (e.g., /product 19960298)\n"
        "- Help: Show help message"
    )
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)
    return CATEGORY

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a help message describing available commands."""
    help_message = (
        f"Welcome to {BOT_USERNAME}!\n"
        "Here are the available commands:\n"
        "/start - Show the welcome message with category and command buttons\n"
        "/deals <category_slug> - View discounted products in a category (e.g., /deals mobile)\n"
        "/product <dkp> - Get details for a specific product (e.g., /product 19960298)\n"
        "/help - Show this help message\n\n"
        "Use the buttons in /start to quickly access categories or commands!"
    )
    await update.effective_message.reply_text(help_message)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle button clicks."""
    query = update.callback_query
    await query.answer()

    if query.data.startswith("category_"):
        category_slug = query.data.split("_")[1]
        products = await get_all_products_by_category(category_slug)
        
        if not products:
            error_message = (
                "No discounted products found in this category.\n"
                "Possible reasons:\n"
                "- No products have discounts in this category.\n"
                "- API authentication failed (check DIGIKALA_TOKEN in .env).\n"
                "- Invalid category slug."
            )
            await query.edit_message_text(error_message)
            return ConversationHandler.END
        
        keyboard = [
            [InlineKeyboardButton(product["title_fa"], callback_data=f"product_{product['id']}")]
            for product in products[:5]
        ]
        keyboard.append([InlineKeyboardButton("Back to Categories", callback_data="back")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        display_name = next((cat["name"] for cat in CATEGORIES if cat["slug"] == category_slug), category_slug.title())
        await query.edit_message_text(
            f"Discounted products in {display_name}:", reply_markup=reply_markup
        )
        return PRODUCTS
    
    elif query.data == "deals":
        await query.edit_message_text("Please provide a category slug (e.g., /deals mobile)")
        return ConversationHandler.END
    elif query.data == "product":
        await query.edit_message_text("Please provide a product DKP (e.g., /product 19960298)")
        return ConversationHandler.END
    elif query.data == "help":
        await help(update, context)
        return ConversationHandler.END
    elif query.data == "back":
        return await start(update, context)
    
    return CATEGORY

async def product_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle product selection."""
    query = update.callback_query
    await query.answer()
    
    product_id = query.data.split("_")[1]
    category_slug = None
    for row in query.message.reply_markup.inline_keyboard:
        for button in row:
            if button.callback_data.startswith("category_"):
                category_slug = button.callback_data.split("_")[1]
                break
        if category_slug:
            break
    
    if category_slug:
        products = await get_all_products_by_category(category_slug)
        product = next((p for p in products if p["id"] == product_id), None)
        
        if product:
            price_text = f"Original Price: {product['main_price']} IRR\nDiscounted Price: {product['discounted_price']} IRR"
            caption = f"Product: {product['title_fa']}\n{price_text}\nLink: {product['url']}"
            try:
                if product['featured_image']:
                    await query.message.reply_photo(
                        photo=product['featured_image'],
                        caption=caption,
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("Back to Categories", callback_data="back")]
                        ])
                    )
                    await query.message.delete()
                else:
                    await query.edit_message_text(
                        f"{caption}\nImage: Not available",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("Back to Categories", callback_data="back")]
                        ])
                    )
            except Exception as e:
                logging.error(f"Error sending product image for {product['id']}: {e}")
                await query.edit_message_text(
                    f"{caption}\nImage: Failed to load",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("Back to Categories", callback_data="back")]
                    ])
                )
        else:
            await query.edit_message_text("Product not found.")
    else:
        await query.edit_message_text("Category not found.")
    
    return PRODUCTS

async def deals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not SHOPAPI_TOKEN:
        await update.message.reply_text("Error: ShopAPI token not configured. Please check DIGIKALA_TOKEN in .env.")
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
            f"No discounted products found in {category_slug}. Try /deals mobile or /product 19960298.\n"
            "If this persists, check DIGIKALA_TOKEN in .env or try another category."
        )

async def product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not SHOPAPI_TOKEN:
        await update.message.reply_text("Error: ShopAPI token not configured. Please check DIGIKALA_TOKEN in .env.")
        return
    if not context.args:
        await update.message.reply_text("Please provide a product DKP (e.g., /product 19960298)")
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
            f"Product with DKP {dkp} not found. Try /product 19960298."
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

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CATEGORY: [CallbackQueryHandler(button_callback, pattern="^category_|^back$")],
            PRODUCTS: [CallbackQueryHandler(product_selected)],
        },
        fallbacks=[CommandHandler("help", help), CommandHandler("deals", deals), CommandHandler("product", product)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("help", help))
    app.add_handler(CommandHandler("deals", deals))
    app.add_handler(CommandHandler("product", product))

    try:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(poll_interval=3, drop_pending_updates=True, timeout=20)
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logging.info("Received KeyboardInterrupt, shutting down...")
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()

if __name__ == "__main__":
    logging.info("Starting the bot...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logging.info("Main loop interrupted, closing...")
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()

        
#TODO: I should add 12 buttons to the main menu, each button should be a category, and when clicked, it should show the products in that category.