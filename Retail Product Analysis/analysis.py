import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="Retail Product Performance", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv("retail_data.csv")
    return df

df = load_data()

# Data Cleaning
df.dropna(inplace=True)
df['date'] = pd.to_datetime(df['date'])
df['sales'] = df['sales'].astype(float)
df['profit'] = df['profit'].astype(float)
df['units_sold'] = df['units_sold'].astype(int)
df['returns'] = df['returns'].astype(int)

# Avoid division by zero
df['units_sold'] = df['units_sold'].replace(0, 1)
df['sales'] = df['sales'].replace(0, 1)


# Metric Calculation
df['profit_margin'] = df['profit'] / df['sales']
df['return_rate'] = df['returns'] / df['units_sold']

# Top & Bottom Performers
def get_top_bottom(df, metric, top_n=10):
    top = df.sort_values(by=metric, ascending=False).head(top_n)
    bottom = df.sort_values(by=metric, ascending=True).head(top_n)
    return top, bottom


category_summary = df.groupby("category").agg({
    "sales": "sum",
    "profit": "sum",
    "profit_margin": "mean",
    "return_rate": "mean"
}).reset_index()

underperforming = category_summary[category_summary['profit_margin'] < 0.1]


st.title(" Retail Product Performance Dashboard")

tabs = st.tabs([" Overview", "Top & Bottom Products", " Category Analysis", "Business Recommendations"])
with tabs[0]:
    st.header(" Key Metrics Overview")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Sales", f"${df['sales'].sum():,.2f}")
    col2.metric("Total Profit", f"${df['profit'].sum():,.2f}")
    col3.metric("Avg. Profit Margin", f"{df['profit_margin'].mean()*100:.2f}%")
    col4.metric("Avg. Return Rate", f"{df['return_rate'].mean()*100:.2f}%")

    st.subheader("Sample of Cleaned Data")
    st.dataframe(df.head(10))

# Top and Bottom Products 
with tabs[1]:
    st.header(" Top & Bottom Performing Products")
    metrics = ["sales", "profit_margin", "return_rate"]
    metric = st.selectbox("Select Metric", metrics)

    top, bottom = get_top_bottom(df, metric)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Top 10 Products")
        st.dataframe(top[['product_name', metric]])
        fig1, ax1 = plt.subplots(figsize=(6, 4))
        sns.barplot(y=top['product_name'], x=top[metric], ax=ax1)
        st.pyplot(fig1)

    with col2:
        st.subheader("Bottom 10 Products")
        st.dataframe(bottom[['product_name', metric]])
        fig2, ax2 = plt.subplots(figsize=(6, 4))
        sns.barplot(y=bottom['product_name'], x=bottom[metric], ax=ax2)
        st.pyplot(fig2)

# Category Analysis
with tabs[2]:
    st.header(" Category-Level Summary")
    st.dataframe(category_summary)

    fig3, ax3 = plt.subplots(1, 2, figsize=(14, 4))
    sns.barplot(data=category_summary, x='category', y='sales', ax=ax3[0])
    ax3[0].set_title("Total Sales by Category")
    sns.barplot(data=category_summary, x='category', y='profit_margin', ax=ax3[1])
    ax3[1].set_title("Avg. Profit Margin by Category")
    st.pyplot(fig3)

    st.subheader(" Underperforming Categories")
    st.dataframe(underperforming)

# Business Recommendations
with tabs[3]:
    st.header(" Actionable Insights")

    st.markdown("""
    - **High Sales, Low Profit Margin**: Consider revisiting pricing or reducing cost of goods sold.
    - **High Return Rate**: Indicates possible quality issues or mismatched customer expectations.
    - **Top Performers**: Allocate more inventory, promotions, or bundles.
    - **Underperforming Categories**: Evaluate for improvement, bundling, or discontinuation.
    """)

    st.subheader(" Summary Table")
    st.dataframe(df[['product_name', 'sales', 'profit', 'profit_margin', 'return_rate']].sort_values(by='sales', ascending=False).head(10))

