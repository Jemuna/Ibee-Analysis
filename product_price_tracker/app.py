from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from scraper import search_all_products, ProductScraper # Updated import
import pandas as pd
import os
from product_scraper import track_product, get_amazon_data
from wishlist_analysis import generate_wishlist_insights
import csv
from bs4 import BeautifulSoup
import requests
import re
import matplotlib.pyplot as plt
import plotly.graph_objs as go
import plotly.offline as pyo
import threading
import time

app = Flask(__name__)
app.secret_key = 'secret_key_123'

# File paths
DATA_FILE = 'price_data.csv'
WISHLIST_FILE = 'wishlist.csv'

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/add_product', methods=['POST'])
def add_product():
    url = request.form['url']
    try:
        threshold = float(request.form['threshold'])
    except ValueError:
        flash("Threshold must be a number.", "danger")
        return redirect(url_for('home'))

    track_product(url, threshold)

    if 'add_to_wishlist' in request.form:
        product_info = scrape_product_details(url)

        file_exists = os.path.isfile(WISHLIST_FILE)
        with open(WISHLIST_FILE, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            if not file_exists or os.path.getsize(WISHLIST_FILE) == 0:
                writer.writerow(['user_id', 'item_name', 'category', 'price_threshold', 'set_date', 'last_activity', 'times_visited', 'intent_score'])
            writer.writerow([
                "user1",
                product_info.get('product_name', ''),
                product_info.get('category', 'Unknown'),
                threshold,
                pd.Timestamp.now().date(),
                pd.Timestamp.now().date(),
                1,
                ''
            ])

    flash("Product scraped successfully!", "success")
    return redirect(url_for('view_products'))

@app.route('/products')
def view_products():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        products = df.to_dict(orient='records')
    else:
        products = []
    return render_template('products.html', products=products)

@app.route('/wishlist', methods=['GET', 'POST'])
def wishlist():
    if request.method == 'POST':
        user_id = request.form['user_id']
        item_name = request.form['item_name']
        category = request.form['category']
        price_threshold = request.form['price_threshold']
        set_date = request.form['set_date']
        last_activity = request.form['last_activity']
        times_visited = request.form['times_visited']
        intent_score = request.form.get('intent_score', '')

        file_exists = os.path.isfile(WISHLIST_FILE)
        with open(WISHLIST_FILE, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            if not file_exists or os.path.getsize(WISHLIST_FILE) == 0:
                writer.writerow(['user_id', 'item_name', 'category', 'price_threshold', 'set_date', 'last_activity', 'times_visited', 'intent_score'])
            writer.writerow([
                user_id, item_name, category, price_threshold,
                set_date, last_activity, times_visited, intent_score
            ])

        return redirect('/wishlist')

    if os.path.exists(WISHLIST_FILE):
        insights = generate_wishlist_insights(WISHLIST_FILE)
        category_summary = insights['category_group']
        price_hist = insights['price_hist']
        intent_counts = insights['intent_counts']
        raw_data = insights['raw_df'].to_dict(orient='records')
    else:
        category_summary = []
        price_hist = {}
        intent_counts = {}
        raw_data = []

    return render_template('wishlist.html',
                           category_summary=category_summary,
                           price_hist=price_hist,
                           intent_counts=intent_counts,
                           wishlist_data=raw_data)

@app.route('/alerts')
def alerts():
    alerts = []
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)

        if 'threshold' in df.columns and 'price' in df.columns:
            df['price'] = pd.to_numeric(df['price'], errors='coerce')
            df['threshold'] = pd.to_numeric(df['threshold'], errors='coerce')
            df.dropna(subset=['price', 'threshold'], inplace=True)

            alerts_df = df[df['price'] < df['threshold']]
            if alerts_df.empty:
                flash("No alerts triggered yet. All prices are above thresholds.", "info")
            alerts = alerts_df.to_dict(orient='records')
        else:
            flash("Threshold or price column not found in data. Please update scraper.", "danger")
    else:
        flash("No product data found yet. Please add a product first.", "warning")

    return render_template('alerts.html', alerts=alerts)

@app.route('/bar_chart')
def bar_chart():
    df = pd.read_csv(DATA_FILE)
    bar_html = plotly_bar_avg_price(df)
    return render_template('bar_chart.html', bar_html=bar_html)

@app.route('/all_graphs')
def all_graphs():
    df = pd.read_csv(DATA_FILE)
    box_plot = create_box_plot(df)
    histogram = create_histogram(df)
    return render_template('all_graphs.html',
                           box_plot=box_plot,
                           histogram=histogram)

@app.route("/search", methods=["GET", "POST"], endpoint='search_products')
def search_products():
    products = None
    loading = False
    search_params = {}
    
    if request.method == "POST":
        product_name = request.form.get("product_name", "").strip()
        price_range = request.form.get("price_range", "all")
        sort_by = request.form.get("sort_by", "price")
        
        search_params = {
            'product_name': product_name,
            'price_range': price_range,
            'sort_by': sort_by
        }
        
        if not product_name:
            flash("Please enter a product name.", "warning")
            return render_template("search.html", products=products, search_params=search_params)
        
        try:
            # Show loading message
            loading = True
            
            # Search with enhanced scraper
            products = search_all_products(product_name, price_range, sort_by)
            
            if not products:
                flash("No products found. Try different keywords or price range.", "info")
            else:
                flash(f"Found {len(products)} products!", "success")
                
        except Exception as e:
            flash(f"Error during search: {str(e)}", "danger")
            print(f"Search error: {e}")
            products = []
    
    return render_template("search.html", 
                          products=products, 
                          loading=loading,
                          search_params=search_params)

# AJAX endpoint for real-time search
@app.route("/api/search", methods=["POST"])
def api_search():
    try:
        data = request.get_json()
        product_name = data.get("product_name", "").strip()
        price_range = data.get("price_range", "all")
        sort_by = data.get("sort_by", "price")
        
        if not product_name:
            return jsonify({"error": "Product name is required"}), 400
        
        products = search_all_products(product_name, price_range, sort_by)
        
        return jsonify({
            "products": products,
            "count": len(products)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/product', methods=['GET'])
def product_page():
    product_url = request.args.get('url') 
    return render_template('product.html', product_url=product_url)


# Utility functions
def plotly_bar_avg_price(df):
    df = df.copy()
    avg_price = df.groupby('name')['price'].mean().reset_index()

    fig = go.Figure([go.Bar(
        x=avg_price['name'],
        y=avg_price['price'],
        marker_color='indigo'
    )])

    fig.update_layout(
        title="Average Price per Product",
        xaxis_title="Product Name",
        yaxis_title="Average Price (₹)",
        xaxis_tickangle=-45
    )

    graph_html = pyo.plot(fig, include_plotlyjs=False, output_type='div')
    return graph_html

def create_box_plot(df):
    fig = go.Figure()

    for product in df['name'].unique():
        product_prices = df[df['name'] == product]['price']
        fig.add_trace(go.Box(
            y=product_prices,
            name=product,
            boxpoints='all',
            jitter=0.5,
            whiskerwidth=0.2,
            marker=dict(size=4),
            line=dict(width=1)
        ))

    fig.update_layout(
        title='Price Range by Product',
        yaxis_title='Price (₹)',
        xaxis_title='Product',
        boxmode='group',
        showlegend=False,
        xaxis_tickangle=-45,
        height=600,
        margin=dict(l=40, r=40, t=60, b=150)
    )

    return pyo.plot(fig, output_type='div')

def create_histogram(df):
    fig = go.Figure()

    for product in df['name'].unique():
        fig.add_trace(go.Histogram(
            x=df[df['name'] == product]['price'],
            name=product,
            opacity=0.6  
        ))

    fig.update_layout(
        title='Price Distribution by Product',
        xaxis_title='Price (₹)',
        yaxis_title='Count',
        barmode='overlay', 
        height=600
    )

    return pyo.plot(fig, output_type='div')

def scrape_product_details(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')

        title = soup.find(id="productTitle")
        price = soup.find("span", {"class": "a-offscreen"})

        product_name = title.get_text(strip=True) if title else "Unknown"
        price_text = price.get_text(strip=True).replace("₹", "").replace(",", "") if price else "0"
        price_value = float(price_text) if price_text.replace('.', '', 1).isdigit() else 0.0

        return {
            "product_name": product_name,
            "price": price_value,
            "category": "General",
        }

    except Exception as e:
        print("Error scraping:", e)
        return {
            "product_name": "Unknown",
            "price": 0.0,
            "category": "Unknown",
        }
    

@app.route("/debug_search", methods=["POST"])
def debug_search():
    product_name = request.form.get("product_name", "").strip()
    price_range = request.form.get("price_range", "all")
    
    if product_name:
        products = search_all_products(product_name, price_range, "price")
        
        # Debug: Print all URLs to console
        print("DEBUG: Found products with URLs:")
        for i, p in enumerate(products):
            print(f"{i+1}. Name: {p['name'][:50]}...")
            print(f"   URL: {p.get('url', 'NO URL')}")
            print(f"   Source: {p.get('source', 'NO SOURCE')}")
            print("---")
        
        # Return JSON for inspection
        return jsonify(products)
    
    return jsonify({"error": "No product name provided"})
   

if __name__ == '__main__':
    app.run(debug=True)