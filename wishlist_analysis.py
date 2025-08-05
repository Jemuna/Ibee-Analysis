# wishlist_analysis.py
import pandas as pd
import matplotlib.pyplot as plt
import os

def generate_wishlist_insights(csv_path="wishlist.csv"):
    df = pd.read_csv(csv_path)

    # Fill missing intent_score
    def classify_intent(row):
        if pd.notnull(row['intent_score']):
            return row['intent_score']
        if row['times_visited'] >= 5 and pd.to_datetime(row['last_activity']) >= pd.Timestamp.now() - pd.Timedelta(days=7):
            return 'high'
        elif row['times_visited'] >= 3:
            return 'medium'
        else:
            return 'low'

    df['intent_score'] = df.apply(classify_intent, axis=1)

    # Group by category
    category_group = df.groupby('category').agg({
        'price_threshold': 'mean',
        'user_id': 'count'
    }).reset_index().rename(columns={
        'price_threshold': 'avg_price',
        'user_id': 'user_count'
    })

    #  Save Histogram (Price Threshold)
    plt.figure(figsize=(6, 4))
    df['price_threshold'].plot(kind='hist', bins=10, color='skyblue', edgecolor='black')
    plt.title("Price Threshold Histogram")
    plt.xlabel("Threshold Price (₹)")
    plt.ylabel("Count")
    plt.tight_layout()
    plt.savefig("static/hist_price.png")
    plt.close()

    # Save Pie Chart (Intent Score Distribution)
    intent_counts = df['intent_score'].value_counts()
    plt.figure(figsize=(6, 6))
    intent_counts.plot(kind='pie', autopct='%1.1f%%', startangle=140)
    plt.title("Intent Score Distribution")
    plt.ylabel("")  # Remove y-label
    plt.tight_layout()
    plt.savefig("static/intent_pie.png")
    plt.close()

    return {
        "category_group": category_group.to_dict(orient="records"),
        "price_hist": df['price_threshold'].tolist(),
        "intent_counts": intent_counts.to_dict(),
        "raw_df": df
    }
