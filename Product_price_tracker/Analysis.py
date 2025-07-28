import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Sample data (can be replaced with actual CSV file reading)
data = {
    'user_id': [101, 102, 103, 104],
    'item_name': ['Redmi Note 12', 'Noise Watch 2', 'Mi TV 43"', 'Philips Trimmer'],
    'category': ['Mobile', 'Smartwatch', 'TV', 'Grooming'],
    'price_threshold': [12000, 3000, 25000, 1200],
    'set_date': ['2024-07-01', '2024-07-05', '2024-06-30', '2024-07-10'],
    'last_activity': ['2024-07-20', '2024-07-15', '2024-07-18', '2024-07-20'],
    'times_visited': [5, 3, 7, 1],
    'intent_score': ['high', 'medium', 'high', 'low']
}

# Create DataFrame
df = pd.DataFrame(data)

# Convert date columns to datetime
df['set_date'] = pd.to_datetime(df['set_date'])
df['last_activity'] = pd.to_datetime(df['last_activity'])

# Function to classify intent_score if missing
def classify_intent(row):
    if pd.isna(row['intent_score']):
        days_since_activity = (datetime.now() - row['last_activity']).days
        visits = row['times_visited']
        
        if visits >= 5 and days_since_activity <= 7:
            return 'high'
        elif visits >= 3 and days_since_activity <= 14:
            return 'medium'
        else:
            return 'low'
    return row['intent_score']

# Apply intent classification
df['intent_score'] = df.apply(classify_intent, axis=1)

# Analysis 1: Group by category
category_analysis = df.groupby('category').agg({
    'price_threshold': 'mean',
    'user_id': 'count'
}).rename(columns={
    'price_threshold': 'avg_price_threshold',
    'user_id': 'user_count'
}).reset_index()

# Analysis 2: Create histogram of price thresholds
plt.figure(figsize=(10, 6))
plt.hist(df['price_threshold'], bins=10, edgecolor='black')
plt.title('Distribution of Price Thresholds')
plt.xlabel('Price Threshold (INR)')
plt.ylabel('Frequency')
plt.savefig('price_threshold_histogram.png')
plt.close()

# Analysis 3: Count users by intent_score
intent_counts = df['intent_score'].value_counts().reset_index()
intent_counts.columns = ['intent_score', 'user_count']

# Save results to CSV
category_analysis.to_csv('category_analysis.csv', index=False)
intent_counts.to_csv('intent_counts.csv', index=False)

# Print results
print("\nCategory Analysis:")
print(category_analysis)
print("\nIntent Score Distribution:")
print(intent_counts)
print("\nHistogram saved as 'price_threshold_histogram.png'")