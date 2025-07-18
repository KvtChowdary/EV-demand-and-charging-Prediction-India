# backend/model_trainer.py (with Model Performance Metrics)

import pandas as pd
from prophet import Prophet
import os
import joblib # For saving and loading models
import holidays # For India-specific holidays
from prophet.diagnostics import cross_validation, performance_metrics # New imports
import json # New import for saving metrics

# Define paths
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
MODELS_DIR = os.path.join(os.path.dirname(__file__), '..', 'model')

# Create models directory if it doesn't exist
os.makedirs(MODELS_DIR, exist_ok=True)

# --- Load Processed Data (Category-wise) ---
print("--- Loading Processed EV Sales Data for Training ---")
processed_file_path = os.path.join(DATA_DIR, 'india_monthly_ev_sales_categories.csv')

try:
    df_category_monthly_sales = pd.read_csv(processed_file_path)
    df_category_monthly_sales['Month_Date'] = pd.to_datetime(df_category_monthly_sales['Month_Date'])
    print("Processed category-wise data loaded successfully.")
    print(df_category_monthly_sales.head())
    print(df_category_monthly_sales.info())

except FileNotFoundError:
    print(f"Error: Processed data file '{processed_file_path}' not found.")
    print("Please ensure 'data_processing.py' was run successfully to create this file.")
    exit()
except Exception as e:
    print(f"An unexpected error occurred during loading processed data: {e}")
    exit()

# Define the categories for which we will train models
relevant_categories = ['2W', '3W', '4W', 'Bus'] # Must match categories from data_processing.py

# --- Prepare Holidays for Prophet ---
min_date = df_category_monthly_sales['Month_Date'].min()
max_date = df_category_monthly_sales['Month_Date'].max()
in_holidays_instance = holidays.CountryHoliday('IN', years=range(min_date.year, max_date.year + 5))

holidays_list = []
for date, name in sorted(in_holidays_instance.items()):
    holidays_list.append({'holiday': name, 'ds': date})
holidays_df_prophet = pd.DataFrame(holidays_list)
holidays_df_prophet['ds'] = pd.to_datetime(holidays_df_prophet['ds'])

if not holidays_df_prophet.empty:
    print(f"\nProphet holidays DataFrame prepared (first 5):")
    print(holidays_df_prophet.head())
else:
    holidays_df_prophet = None
    print("No holidays detected/generated to add to Prophet model.")

# --- Train and Save Models for Each Category + Calculate Metrics ---
trained_models = {}
all_metrics = {} # Dictionary to store metrics for each category

print("\n--- Training Prophet Models for Each EV Category ---")
for category in relevant_categories:
    column_name = f'{category}_EV_Sales'
    if column_name not in df_category_monthly_sales.columns:
        print(f"Warning: Column '{column_name}' not found for training. Skipping {category} model.")
        continue

    df_prophet_category = df_category_monthly_sales[['Month_Date', column_name]].rename(columns={'Month_Date': 'ds', column_name: 'y'})

    print(f"\nTraining model for {category}...")
    model = Prophet(
        holidays=holidays_df_prophet,
        seasonality_mode='additive',
        daily_seasonality=False,
        weekly_seasonality=False
    )

    model.fit(df_prophet_category)
    trained_models[category] = model
    print(f"Prophet model for {category} trained successfully.")

    # --- Calculate Performance Metrics ---
    print(f"Calculating performance metrics for {category} model...")
    # Initial period: data range, period: step for cutoff, horizon: how far to predict for evaluation
    # Horizon should be less than or equal to future_months in prediction endpoint
    # For monthly data, 12 periods is 1 year.
    try:
        # We need enough history for cross-validation. Let's aim for 2 years initial, 1 year period, 1 year horizon
        # Adjust these based on your data's length and desired evaluation window.
        # df_prophet_category length check for CV
        if len(df_prophet_category) > 36: # At least 3 years of data
            df_cv = cross_validation(
                model,
                initial='730 days', # 2 years initial training data
                period='180 days',  # Retrain every 6 months
                horizon='365 days', # Predict 1 year into future for evaluation
                parallel="processes" # Use parallel processing for faster CV
            )
            df_p = performance_metrics(df_cv)

            # Store key metrics
            metrics = {
                'mae': df_p['mae'].mean(),
                'rmse': df_p['rmse'].mean(),
                'mape': df_p['mape'].mean(),
                'horizon': '365 days' # Document the horizon for which metrics are valid
            }
            all_metrics[category] = metrics
            print(f"Metrics for {category}: MAE={metrics['mae']:.2f}, RMSE={metrics['rmse']:.2f}, MAPE={metrics['mape']:.2f}")
        else:
            print(f"Not enough data for robust cross-validation for {category}. Skipping metrics calculation.")
            all_metrics[category] = {"status": "Not enough data for cross-validation"}

    except Exception as e:
        print(f"Error during cross-validation or metrics calculation for {category}: {e}")
        all_metrics[category] = {"status": f"Error during metrics calculation: {str(e)}"}


    # Save the trained model for this category
    model_filename = f'prophet_ev_sales_model_{category.lower()}.pkl'
    model_path = os.path.join(MODELS_DIR, model_filename)
    try:
        joblib.dump(model, model_path)
        print(f"Trained model for {category} saved to: {model_path}")
    except Exception as e:
        print(f"Error saving model for {category}: {e}")

print("\n--- All Category Models Training Complete. ---")

# Save a list of relevant categories to easily load in main.py
joblib.dump(relevant_categories, os.path.join(MODELS_DIR, 'relevant_categories.pkl'))
print(f"List of relevant categories saved to: {os.path.join(MODELS_DIR, 'relevant_categories.pkl')}")

# --- Save All Metrics to a JSON file ---
metrics_file_path = os.path.join(MODELS_DIR, 'model_performance_metrics.json')
try:
    with open(metrics_file_path, 'w') as f:
        json.dump(all_metrics, f, indent=4)
    print(f"Model performance metrics saved to: {metrics_file_path}")
except Exception as e:
    print(f"Error saving model metrics: {e}")


print("\n--- Model Training & Metrics Calculation Complete. Models and Metrics are ready. ---")