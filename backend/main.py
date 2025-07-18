# --- COPY FROM HERE ---
# backend/main.py (Previous Version - NO WHAT-IF SCENARIOS)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import joblib
import pandas as pd
from prophet import Prophet
import os
from datetime import datetime, timedelta
from typing import Union, List # No Optional needed here as multipliers are removed
import holidays
import json


MODELS_DIR = os.path.join(os.path.dirname(__file__), '..', 'model')
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
PROCESSED_DATA_PATH = os.path.join(DATA_DIR, 'india_monthly_ev_sales_categories.csv')
METRICS_PATH = os.path.join(MODELS_DIR, 'model_performance_metrics.json')

app = FastAPI(
    title="EV Charging Demand Prediction API (India)",
    description="API for predicting Electric Vehicle sales trends and estimated charging demand in India.",
    version="1.0.0"
)

origins = [
    "http://localhost",
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

trained_models = {}
last_historical_date = None
relevant_categories = []
model_performance_metrics = {}


EV_ENERGY_CONSUMPTION_KWH_PER_MONTH = {
    '2W': 45,
    '3W': 225,
    '4W': 280,
    'Bus': 4500
}


try:
    print(f"Attempting to load relevant categories from: {os.path.join(MODELS_DIR, 'relevant_categories.pkl')}")
    relevant_categories = joblib.load(os.path.join(MODELS_DIR, 'relevant_categories.pkl'))
    print(f"Relevant categories loaded: {relevant_categories}")

    for category in relevant_categories:
        model_filename = f'prophet_ev_sales_model_{category.lower()}.pkl'
        model_path = os.path.join(MODELS_DIR, model_filename)
        print(f"Attempting to load model for {category} from: {model_path}")
        trained_models[category] = joblib.load(model_path)
        print(f"Prophet model for {category} loaded successfully!")

except FileNotFoundError as e:
    print(f"ERROR: Model file or categories list not found: {e}. Please ensure model_trainer.py was run to create these files.")
except Exception as e:
    print(f"ERROR loading models: {e}")

try:
    print(f"Attempting to load processed data from: {PROCESSED_DATA_PATH}")
    df_history_all_categories = pd.read_csv(PROCESSED_DATA_PATH)
    df_history_all_categories['Month_Date'] = pd.to_datetime(df_history_all_categories['Month_Date'])
    last_historical_date = df_history_all_categories['Month_Date'].max()
    print(f"Historical data loaded. Last historical date: {last_historical_date}")
except FileNotFoundError:
    print(f"ERROR: Processed data file not found at {PROCESSED_DATA_PATH}. Please ensure data_processing.py was run to create this file.")
    df_history_all_categories = pd.DataFrame()
    last_historical_date = None
except Exception as e:
    print(f"ERROR loading historical data: {e}")

try:
    print(f"Attempting to load model performance metrics from: {METRICS_PATH}")
    with open(METRICS_PATH, 'r') as f:
        model_performance_metrics = json.load(f)
    print("Model performance metrics loaded successfully!")
except FileNotFoundError:
    print(f"ERROR: Metrics file not found at {METRICS_PATH}. Please ensure model_trainer.py was run to create this file.")
except Exception as e:
    print(f"ERROR loading model performance metrics: {e}")


class PredictionRequest(BaseModel):
    future_months: int = Field(..., gt=0, description="Number of months into the future to predict.")


class CategoryPrediction(BaseModel):
    category: str
    predicted_sales: float
    predicted_charging_demand_kwh: float

class OverallPredictionResponse(BaseModel):
    date: str = Field(..., example="2025-01-01", description="Date of the prediction.")
    total_predicted_sales: float = Field(..., description="Predicted total EV sales for the month (all categories).")
    total_predicted_charging_demand_kwh: float = Field(..., description="Estimated total EV charging demand in kWh for the month (all categories).")
    category_breakdown: List[CategoryPrediction] = Field(..., description="Breakdown of predictions by vehicle category.")
    lower_bound_total_sales: float = Field(..., description="Lower bound of the total predicted sales interval (sum of yhat_lower).")
    upper_bound_total_sales: float = Field(..., description="Upper bound of the total predicted sales interval (sum of yhat_upper).")

class ModelMetricsResponse(BaseModel):
    category: str
    mae: Union[float, str] = Field(..., description="Mean Absolute Error or status if not calculated.")
    rmse: Union[float, str] = Field(..., description="Root Mean Squared Error or status if not calculated.")
    mape: Union[float, str] = Field(..., description="Mean Absolute Percentage Error or status if not calculated.")
    horizon: Union[str, None] = Field(None, description="Prediction horizon for which metrics are valid.")
    status: Union[str, None] = Field(None, description="Status message if metrics calculation failed.")

class HealthCheckResponse(BaseModel):
    status: str
    models_loaded: bool
    metrics_loaded: bool
    last_historical_date: Union[str, None]
    categories_loaded: List[str]
    errors: Union[str, None]


@app.get("/", summary="Root Endpoint")
async def read_root():
    return {"message": "Welcome to the EV Charging Demand Prediction Backend API! Visit /docs for API documentation."}

@app.get("/health", response_model=HealthCheckResponse, summary="Health Check")
async def health_check():
    status = "ok"
    errors = []
    if not trained_models:
        status = "degraded"
        errors.append("No prediction models loaded.")
    if not model_performance_metrics:
        status = "degraded"
        errors.append("Model performance metrics not loaded.")
    if last_historical_date is None:
        status = "degraded"
        errors.append("Historical data not loaded.")
    if not relevant_categories:
        status = "degraded"
        errors.append("No relevant categories loaded.")

    return HealthCheckResponse(
        status=status,
        models_loaded=bool(trained_models),
        metrics_loaded=bool(model_performance_metrics),
        last_historical_date=str(last_historical_date) if last_historical_date else None,
        categories_loaded=relevant_categories,
        errors = ", ".join(errors) if errors else None
    )

@app.get("/model_metrics", response_model=List[ModelMetricsResponse], summary="Get Model Performance Metrics")
async def get_model_metrics():
    if not model_performance_metrics:
        raise HTTPException(status_code=500, detail="Model performance metrics not loaded. Please ensure model_trainer.py was run.")

    response_metrics = []
    for category, metrics in model_performance_metrics.items():
        if "status" in metrics:
            response_metrics.append(ModelMetricsResponse(
                category=category,
                mae="N/A",
                rmse="N/A",
                mape="N/A",
                status=metrics["status"],
                horizon=metrics.get("horizon")
            ))
        else:
            response_metrics.append(ModelMetricsResponse(
                category=category,
                mae=metrics['mae'],
                rmse=metrics['rmse'],
                mape=metrics['mape'],
                horizon=metrics.get('horizon')
            ))
    return response_metrics


@app.post("/predict_ev_charging_demand", response_model=List[OverallPredictionResponse], summary="Predict EV Sales & Charging Demand")
async def predict_ev_charging_demand(request: PredictionRequest):
    if not trained_models:
        raise HTTPException(status_code=500, detail="Prediction models not loaded. Please ensure model_trainer.py was run successfully.")
    if last_historical_date is None:
        raise HTTPException(status_code=500, detail="Historical data not loaded. Cannot determine prediction start date. Please ensure data_processing.py was run successfully.")
    if df_history_all_categories.empty:
        raise HTTPException(status_code=500, detail="Historical data DataFrame is empty. Cannot generate predictions.")


    future_dates = pd.date_range(
        start=last_historical_date + pd.offsets.MonthBegin(1),
        periods=request.future_months,
        freq='MS'
    )
    future = pd.DataFrame({'ds': future_dates})

    in_holidays_future = holidays.CountryHoliday('IN', years=range(future_dates.min().year, future_dates.max().year + 1))
    holidays_df_future = pd.DataFrame([{'holiday': name, 'ds': date} for date, name in sorted(in_holidays_future.items())])
    holidays_df_future['ds'] = pd.to_datetime(holidays_df_future['ds'])
    
    category_forecasts = {}
    for category, model_instance in trained_models.items():
        forecast = model_instance.predict(future)
        # Multipliers removed from here, default is 1.0
        
        category_forecasts[category] = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].rename(columns={'yhat': 'predicted_sales', 'yhat_lower': 'lower_bound', 'yhat_upper': 'upper_bound'})

    final_predictions = []
    for i, ds_date in enumerate(future_dates):
        current_date_str = f"{ds_date.year:04d}-{ds_date.month:02d}-01"

        total_monthly_sales = 0
        total_monthly_charging_demand_kwh = 0
        current_category_breakdown = []
        
        current_yhat_sum = 0
        current_yhat_lower_sum = 0
        current_yhat_upper_sum = 0

        for category in relevant_categories:
            if category in category_forecasts:
                pred_row = category_forecasts[category].iloc[i]
                
                predicted_sales_cat = max(0, round(pred_row['predicted_sales'], 0))
                lower_bound_cat = max(0, round(pred_row['lower_bound'], 0))
                upper_bound_cat = max(0, round(pred_row['upper_bound'], 0))

                estimated_kwh_per_vehicle = EV_ENERGY_CONSUMPTION_KWH_PER_MONTH.get(category, 0)
                predicted_charging_demand_cat = predicted_sales_cat * estimated_kwh_per_vehicle

                current_category_breakdown.append(
                    CategoryPrediction(
                        category=category,
                        predicted_sales=predicted_sales_cat,
                        predicted_charging_demand_kwh=round(predicted_charging_demand_cat, 0)
                    )
                )
                total_monthly_sales += predicted_sales_cat
                total_monthly_charging_demand_kwh += predicted_charging_demand_cat

                current_yhat_sum += pred_row['predicted_sales']
                current_yhat_lower_sum += pred_row['lower_bound']
                current_yhat_upper_sum += pred_row['upper_bound']

        final_predictions.append(
            OverallPredictionResponse(
                date=current_date_str,
                total_predicted_sales=round(total_monthly_sales, 0),
                total_predicted_charging_demand_kwh=round(total_monthly_charging_demand_kwh, 0),
                category_breakdown=current_category_breakdown,
                lower_bound_total_sales=round(current_yhat_lower_sum, 0),
                upper_bound_total_sales=round(current_yhat_upper_sum, 0)
            )
        )
    return final_predictions
# --- TO HERE ---