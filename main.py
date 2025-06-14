import requests
from bs4 import BeautifulSoup
import streamlit as st
import sqlite3

# Set page configuration at the top
st.set_page_config(page_title="DealScraper", page_icon="🛒")

# Display the logo at the top (adjust path if needed)
st.image(r"logo.jpeg", use_container_width=True)

# Add custom CSS styles
st.markdown(
    """
    <style>
    .black-strip {
        background-color: black;
        color: white;
        padding: 20px;
        width: 100%;
        text-align: center;
        font-size: 35px;
        font-weight: bold;
        border-radius: 2px;
    }
    .product-card {
        border-radius: 10px;
        padding: 15px;
        margin: 10px;
        box-shadow: 0 0 10px rgba(0,0,0,0.1);
        overflow: hidden;
        position: relative;
        display: flex;
        flex-direction: column;
        background-color: white;
        cursor: pointer;
        text-decoration: none;
        color: inherit;
        height: auto;
        min-height: 260px;
    }
    .product-card:hover {
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    .product-image {
        width: 100%;
        aspect-ratio: 1 / 1;
        object-fit: contain;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    .product-title {
        font-weight: bold;
        font-size: 14px;
        color: black;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        height: 40px;
        transition: all 0.3s ease;
    }
    .product-card:hover .product-title {
        -webkit-line-clamp: unset;
        overflow-y: auto;
        max-height: 120px;
    }
    .product-details {
        font-size: 12px;
        color: gray;
        overflow: hidden;
    }
    .load-more-btn {
        text-align: center;
        margin-top: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Page Title
st.markdown('<div class="black-strip"> Find the best deals online </div>', unsafe_allow_html=True)

# Store and Category Selection
stores = ["Flipkart", "Amazon", "Paytm", "Foodpanda", "Freecharge", "Paytmmall"]
categories = ["All Categories", "Beauty and Personal Care", "Electronics", "Grocery", "Recharge"]
deal_sections = ["All Deals", "Hot Deals Online", "Popular Deals"]

# Initialize session state variables if they don't exist
if "store" not in st.session_state:
    st.session_state.store = stores[0]
if "category" not in st.session_state:
    st.session_state.category = categories[0]
if "deal_section" not in st.session_state:
    st.session_state.deal_section = deal_sections[0]
if "current_page" not in st.session_state:
    st.session_state.current_page = 1
if "all_products" not in st.session_state:
    st.session_state.all_products = []

# Callbacks for updating selections
def update_store():
    st.session_state.store = st.session_state.store_widget
    st.session_state.current_page = 1
    st.session_state.all_products = []

def update_category():
    st.session_state.category = st.session_state.category_widget
    st.session_state.current_page = 1
    st.session_state.all_products = []

def update_deal_section():
    st.session_state.deal_section = st.session_state.deal_section_widget
    st.session_state.current_page = 1
    st.session_state.all_products = []

# Create dropdowns with callbacks
st.selectbox("Select Store", stores, key="store_widget", on_change=update_store)
st.selectbox("Select Category", categories, key="category_widget", on_change=update_category)
st.selectbox("Select Deal Section", deal_sections, key="deal_section_widget", on_change=update_deal_section)

# Scraper Function
def scrape_deals(store, category, deal_section, page):
    """Scrape product deals from DealsHeaven."""
    products = []

    # Construct URL based on store, category, and deal section
    if deal_section == "All Deals":
        if category == "All Categories":
            url = f"https://dealsheaven.in/store/{store.lower()}?page={page}"
        else:
            formatted_category = category.lower().replace(" ", "-")
            url = f"https://dealsheaven.in/category/{formatted_category}?page={page}"
    else:
        formatted_deal_section = deal_section.lower().replace(" ", "-")
        if category == "All Categories":
            url = f"https://dealsheaven.in/{formatted_deal_section}?page={page}"
        else:
            formatted_category = category.lower().replace(" ", "-")
            url = f"https://dealsheaven.in/{formatted_deal_section}/{formatted_category}?page={page}"

    # Fetch page content
    response = requests.get(url)
    if response.status_code != 200:
        st.warning(f"Failed to retrieve page {page}. Skipping...")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    all_items = soup.find_all("div", class_="product-item-detail")

    if not all_items:
        st.warning(f"No products found on page {page}.")
        return []

    for item in all_items:
        product = {
            "Title": item.find("h3", title=True)["title"].replace("[Apply coupon]", "").strip() if item.find("h3", title=True) else "N/A",
            "Image": item.find("img", {"data-src": True})["data-src"] if item.find("img", {"data-src": True}) else "https://via.placeholder.com/150",
            "Discount": item.find("div", class_="discount").text.strip() if item.find("div", class_="discount") else "N/A",
            "Special Price": item.find("p", class_="spacail-price").text.strip().replace(",", "") if item.find("p", class_="spacail-price") else "N/A",
            "Category": item.find("a", title=True).get("title", "Uncategorized") if item.find("a", title=True) else "Uncategorized",
            "Link": item.find("a", href=True)["href"] if item.find("a", href=True) else "N/A",
        }

        # Skip products with missing essential fields
        if (
            product["Title"] != "N/A"
            and product["Image"] != "https://via.placeholder.com/150"
            and product["Discount"] != "N/A"
            and product["Special Price"] != "N/A"
            and product["Link"] != "N/A"
        ):
            products.append(product)

    return products

# Display Deals
st.write("### Filtered Deals")
if st.session_state.all_products:
    for i in range(0, len(st.session_state.all_products), 4):
        cols = st.columns(4)
        for col, product in zip(cols, st.session_state.all_products[i:i + 4]):
            with col:
                st.markdown(
                    f"""
                    <a href="{product['Link']}" target="_blank" class="product-card">
                        <img src="{product['Image']}" class="product-image" alt="{product['Title']}"/>
                        <div class="product-title">{product['Title']}</div>
                        <div class="product-details"><strong>Discount:</strong> {product['Discount']}</div>
                        <div class="product-details"><strong>Special Price:</strong> {product['Special Price']}</div>
                    </a>
                    """,
                    unsafe_allow_html=True,
                )
else:
    st.info("No deals loaded. Click 'Load More Deals' to fetch deals.")

# Load More Deals Button (now placed **below** the filtered deals)
st.markdown('<div class="load-more-btn">', unsafe_allow_html=True)
if st.button("Load More Deals"):
    new_products = scrape_deals(st.session_state.store, st.session_state.category, st.session_state.deal_section, st.session_state.current_page)
    if new_products:
        st.session_state.all_products.extend(new_products)
        st.session_state.current_page += 1
st.markdown('</div>', unsafe_allow_html=True)
