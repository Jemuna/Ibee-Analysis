from flask import Flask, render_template, request, redirect, url_for, flash
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

app = Flask(__name__)
app.secret_key = 'secret_key_123'  # required for flash messages

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
                "user1",  # default user
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
        # collect form data
        user_id = request.form['user_id']
        item_name = request.form['item_name']
        category = request.form['category']
        price_threshold = request.form['price_threshold']
        set_date = request.form['set_date']
        last_activity = request.form['last_activity']
        times_visited = request.form['times_visited']
        intent_score = request.form.get('intent_score', '')

        # write data to CSV
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

    # GET request - read and analyze wishlist
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


# Box Plot - Price range of all products

def create_box_plot(df):
    fig = go.Figure()

    # Group prices by product and create a box trace for each product
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


# Histogram - Distribution of product prices
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





@app.route('/all_graphs')
def all_graphs():
    df = pd.read_csv(DATA_FILE)

    box_plot = create_box_plot(df)
    histogram = create_histogram(df)
   

    return render_template('all_graphs.html',
                           box_plot=box_plot,
                           histogram=histogram,
                          )




def scrape_product_details(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Amazon example (update for other sites as needed)
        title = soup.find(id="productTitle")
        price = soup.find("span", {"class": "a-offscreen"})

        product_name = title.get_text(strip=True) if title else "Unknown"
        price_text = price.get_text(strip=True).replace("₹", "").replace(",", "") if price else "0"
        price_value = float(price_text) if price_text.replace('.', '', 1).isdigit() else 0.0

        return {
            "product_name": product_name,
            "price": price_value,
            "category": "General"
        }

    except Exception as e:
        print("Error scraping:", e)
        return {
            "product_name": "Unknown",
            "price": 0.0,
            "category": "Unknown"
        }


import plotly.graph_objs as go
import plotly.offline as pyo

def plotly_price_trend_all(df):
    df = df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['month'] = df['timestamp'].dt.to_period('M')
    monthly = df.groupby(['month', 'name'])['price'].mean().reset_index()
    monthly['month'] = monthly['month'].astype(str)

    traces = []
    for name in monthly['name'].unique():
        product_data = monthly[monthly['name'] == name]
        trace = go.Scatter(
            x=product_data['month'],
            y=product_data['price'],
            mode='lines+markers',
            name=name
        )
        traces.append(trace)

    layout = go.Layout(
        title='Monthly Price Trend for All Products',
        xaxis=dict(title='Month'),
        yaxis=dict(title='Avg Price (₹)'),
        hovermode='closest'
    )

    fig = go.Figure(data=traces, layout=layout)
    graph_html = pyo.plot(fig, include_plotlyjs=False, output_type='div')
    return graph_html


def plot_price_trend(df, product_name):
    sub = df[df['name'] == product_name]
    if sub.empty:
        return None
    sub['timestamp'] = pd.to_datetime(sub['timestamp'])
    sub['month'] = sub['timestamp'].dt.to_period('M')
    monthly = sub.groupby('month')['price'].mean()
    plt.figure(figsize=(8,4))
    monthly.plot(marker='o', linestyle='-', color='dodgerblue')
    plt.title(f"{product_name} - Monthly Price Trend")
    plt.xlabel("Month")
    plt.ylabel("Avg Price (₹)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    filename = f"static/trend_{re.sub(r'\\W+','',product_name)}.png"
    plt.savefig(filename)
    plt.close()
    return filename

@app.route('/product_trends', methods=['GET', 'POST'])
def product_trends():
    df = pd.read_csv(DATA_FILE)
    trend_html = None

    if request.method == 'POST':
        trend_html = plotly_price_trend_all(df)

    return render_template('trends_plotly.html', trend_html=trend_html)







if __name__ == '__main__':
    app.run(debug=True)
