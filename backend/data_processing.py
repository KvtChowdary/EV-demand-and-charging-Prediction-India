# backend/data_processing.py (FINAL UPDATED VERSION with refined category_map and duplicate column fix)

import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns
import holidays # For India-specific holidays

# Define the path to your data directory relative to the project root
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

# --- Load India EV Sales Data ---
print("--- Loading India EV Sales Data ---")

file_name = 'EV_Sales_India_Statewise_AllYears.csv.csv' # Use the exact filename
file_path = os.path.join(DATA_DIR, file_name)

try:
    df_ev_sales = pd.read_csv(file_path)
    print(f"'{file_name}' loaded successfully.")

except FileNotFoundError:
    print(f"Error: The file '{file_name}' was not found in '{os.path.abspath(DATA_DIR)}'.")
    print("Please ensure the downloaded CSV is named exactly 'EV_Sales_India_Statewise_AllYears.csv.csv' and is in the 'data' folder.")
    exit()
except Exception as e:
    print(f"An unexpected error occurred during data loading: {e}")
    exit()

# --- DEBUGGING: Inspect Raw Vehicle Class/Type Distribution ---
print("\n--- DEBUGGING: Unique values and counts for 'Vehicle Class' (Top 20) ---")
print(df_ev_sales['Vehicle Class'].value_counts().head(20))

print("\n--- DEBUGGING: Unique values and counts for 'Vehicle Type' (Top 20) ---")
print(df_ev_sales['Vehicle Type'].value_counts().head(20))
# --- END DEBUGGING SECTION ---


# --- Data Cleaning and Preprocessing ---
print("\n--- Data Cleaning and Preprocessing ---")

# 1. Convert 'Date' column to datetime objects
df_ev_sales['Date'] = pd.to_datetime(df_ev_sales['Date'], errors='coerce')
df_ev_sales.dropna(subset=['Date'], inplace=True)
print(f"Converted 'Date' column to datetime. Remaining rows: {len(df_ev_sales)}")

# 2. Fill minor missing values for categorical columns
for col in ['Vehicle Category', 'Vehicle Type', 'Vehicle Use type']:
    if col in df_ev_sales.columns and df_ev_sales[col].isnull().any():
        df_ev_sales[col].fillna('Unknown', inplace=True)
        print(f"Filled missing values in '{col}' with 'Unknown'.")

# 3. Ensure ELECTRIC(BOV) is numeric
ev_col = 'ELECTRIC(BOV)'
if ev_col in df_ev_sales.columns:
    df_ev_sales[ev_col] = pd.to_numeric(df_ev_sales[ev_col], errors='coerce').fillna(0).astype(int)
else:
    print(f"Warning: Column '{ev_col}' not found. Cannot process EV sales.")
    exit()

# IMPORTANT: Create Month_Date on df_ev_sales before filtering
df_ev_sales['Month_Date'] = df_ev_sales['Date'].dt.to_period('M').dt.to_timestamp()


# --- Identify and Aggregate EV Sales by Major Vehicle Categories ---
# REFINED category_map based on your 'Vehicle Class' DEBUGGING output
category_map = {
    'M-CYCLE/SCOOTER': '2W',
    'MOPED': '2W',
    'MOTORIZED CYCLE (CC > 25CC)': '2W', # Assuming some electric 2Ws might fall here
    'MOTOR CAR': '4W',
    'MOTOR CAB': '4W', # Often used for electric taxis/cabs
    'MAXI CAB': '4W', # Often used for larger electric taxis/cabs
    'THREE WHEELER (PASSENGER)': '3W',
    'THREE WHEELER (GOODS)': '3W',
    'E-RICKSHAW(P)': '3W', # Explicit E-Rickshaw (Passenger)
    'AUTO RICKSHAW': '3W', # Covers general auto-rickshaws, often includes electric
    'BUS': 'Bus',
    'OMNIBUS': 'Bus', # Includes many types of buses
}

# Apply mapping to 'Vehicle Class' to get simplified category
df_ev_sales['Simplified_Category'] = df_ev_sales['Vehicle Class'].str.upper().map(category_map).fillna('Others')

print("\nSimplified_Category distribution (top 10, after REFINED mapping):")
print(df_ev_sales['Simplified_Category'].value_counts().head(10))

# Filter for relevant EV categories (excluding 'Others' that are not common EVs or very niche)
relevant_categories = ['2W', '3W', '4W', 'Bus'] # These are the categories we will model
df_ev_relevant = df_ev_sales[df_ev_sales['Simplified_Category'].isin(relevant_categories)].copy()

# Sum ELECTRIC(BOV) for each simplified category monthly and unstack
# This creates columns like '2W', '3W', '4W', 'Bus'
df_category_monthly_sales = df_ev_relevant.groupby(['Month_Date', 'Simplified_Category'])[ev_col].sum().unstack(fill_value=0)

# Reset index to make 'Month_Date' a regular column and flatten column names
# The column names after reset_index() will be 'Month_Date', '2W', '3W', '4W', 'Bus' etc.
df_category_monthly_sales = df_category_monthly_sales.reset_index()

# Rename these columns to add '_EV_Sales' suffix, avoiding duplicates
rename_map = {cat: f'{cat}_EV_Sales' for cat in df_category_monthly_sales.columns if cat in relevant_categories}
df_category_monthly_sales = df_category_monthly_sales.rename(columns=rename_map)


# Ensure all relevant_categories columns exist (in case a category had 0 sales for all time and wasn't unstacked)
for cat in relevant_categories:
    col_name = f'{cat}_EV_Sales'
    if col_name not in df_category_monthly_sales.columns:
        df_category_monthly_sales[col_name] = 0 # Add column with 0 if it doesn't exist

# Add is_holiday feature to this new aggregated DataFrame
min_year = df_category_monthly_sales['Month_Date'].min().year
max_year = df_category_monthly_sales['Month_Date'].max().year + 2 # Get holidays for future years too
in_holidays = holidays.CountryHoliday('IN', years=range(min_year, max_year + 1))
df_category_monthly_sales['is_holiday'] = df_category_monthly_sales['Month_Date'].apply(lambda x: x in in_holidays).astype(int)

# Create a total EV sales column (summing across identified categories)
df_category_monthly_sales['Total_EV_Sales'] = df_category_monthly_sales[[f'{cat}_EV_Sales' for cat in relevant_categories]].sum(axis=1)


print("\nAggregated category-wise monthly EV sales time series (first 5 rows):")
print(df_category_monthly_sales.head())
print("\nInfo for aggregated category-wise data:")
print(df_category_monthly_sales.info())


# --- Save Processed DataFrame (for all categories) ---
processed_output_path_all_categories = os.path.join(DATA_DIR, 'india_monthly_ev_sales_categories.csv')
df_category_monthly_sales.to_csv(processed_output_path_all_categories, index=False)
print(f"\nProcessed category-wise monthly EV sales data saved to '{processed_output_path_all_categories}'.")

# --- Initial Visualization of Total Time Series ---
print("\n--- Generating Initial Total Time Series Plot ---")
plt.figure(figsize=(14, 7))
sns.lineplot(x='Month_Date', y='Total_EV_Sales', data=df_category_monthly_sales)
plt.title('Total Monthly National EV Sales in India (All Categories)')
plt.xlabel('Date')
plt.ylabel('Total EV Sales')
plt.grid(True)
plt.tight_layout()
plots_dir = os.path.join(os.path.dirname(__file__), '..', 'plots')
os.makedirs(plots_dir, exist_ok=True)
plt.savefig(os.path.join(plots_dir, 'total_monthly_national_ev_sales.png'))
plt.close() # Close plot to prevent it from holding up execution in some environments
print(f"Total EV Sales plot saved to: {os.path.join(plots_dir, 'total_monthly_national_ev_sales.png')}")

# --- Optional: Visualize individual category trends (for your analysis) ---
print("\n--- Generating Individual Category EV Sales Plots (Optional) ---")
for category in relevant_categories:
    plt.figure(figsize=(12, 6))
    sns.lineplot(x='Month_Date', y=f'{category}_EV_Sales', data=df_category_monthly_sales)
    plt.title(f'Monthly National EV Sales in India ({category})')
    plt.xlabel('Date')
    plt.ylabel('EV Sales')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, f'monthly_national_ev_sales_{category.lower()}.png'))
    plt.close()
    print(f"Plot for {category} saved to: {os.path.join(plots_dir, f'monthly_national_ev_sales_{category.lower()}.png')}")


print("\n--- Data Preprocessing and Aggregation Complete. Ready for Model Training per category. ---")