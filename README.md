EV Charging Demand Prediction for India
Project Overview
This project implements a full-stack Artificial Intelligence/Machine Learning (AI/ML) application designed to predict Electric Vehicle (EV) sales trends and estimate the associated charging demand in India. Leveraging historical data and time-series forecasting models, the application provides valuable insights for urban planners, energy providers, and EV infrastructure developers in the rapidly growing Indian EV market.

Features
India-Specific Data: Utilizes official EV registration data from India (Vahan Dashboard) for highly relevant forecasts.
Category-wise Prediction: Forecasts EV sales for major vehicle categories: 2-Wheelers (2W), 3-Wheelers (3W), 4-Wheelers (4W/Cars), and Buses.
Estimated Charging Demand: Converts predicted EV sales into estimated monthly energy consumption (kWh) based on researched average vehicle usage assumptions for India.
Time Series Forecasting: Employs Prophet (by Facebook), a robust time series forecasting model, to capture trends, seasonality, and holiday effects.
Model Performance Metrics: Displays key accuracy metrics (Mean Absolute Error - MAE, Root Mean Squared Error - RMSE, Mean Absolute Percentage Error - MAPE) for each trained model, offering transparency on prediction reliability and highlighting data limitations (e.g., for sparse categories like Buses).
Interactive Web Interface: A user-friendly React frontend allows users to specify prediction horizons and visualize complex results through dynamic charts that show both historical and forecasted data.
Professional & Impressive Design: Features a clean, modern UI with a refined color palette, subtle animations, and an intuitive layout for an engaging user experience.
API-driven Architecture: A robust FastAPI backend serves predictions and metrics via well-defined RESTful APIs, ensuring modularity, scalability, and ease of integration.
Technical Stack
Backend: Python 3.x, FastAPI, Uvicorn
Machine Learning: Pandas, Prophet (by Facebook), Scikit-learn, Joblib (for model persistence)
Frontend: React.js, Chart.js (with react-chartjs-2), HTML, CSS
Environment Management: pip, npm, Virtual Environments (venv)
Data Sources: Vahan Dashboard (via Climate Trends portal), Reserve Bank of India / Trading Economics (for CPI), Python holidays library.
Deployment: (To be determined - e.g., Docker, Render.com, Netlify, Google Cloud Run)
Data Sources
EV Sales/Registration Data: Monthly, category-wise EV sales data for India.
File: EV_Sales_India_Statewise_AllYears.csv.csv
Original Source: Vahan Dashboard (Ministry of Road Transport & Highways, Government of India), aggregated and provided by Climate Trends.
Consumer Price Index (CPI): Monthly historical CPI data for India.
File: All India Consumer Price Index.csv
Source: Trading Economics (aggregates official data like NSO/RBI). Used as an external regressor in the models.
Indian Public Holidays: Used to account for holiday effects on sales patterns.
Source: Python holidays library.
Setup and Local Execution Guide
Follow these steps to set up and run the project on your local machine.

1. Project Folder Structure
Ensure your project root EV_Charging_Demand_Prediction/ has these main subfolders

2. Backend Setup (Python Environment & Dependencies)
Open your EV_Charging_Demand_Prediction project folder in VS Code.
Open a VS Code Terminal (Terminal > New Terminal). This will be your Backend Terminal.
Navigate to the backend directory:
cd backend
Create a Python Virtual Environment:
python -m venv venv
Activate the Virtual Environment:
For Command Prompt: .\venv\Scripts\activate.bat
For PowerShell: .\venv\Scripts\Activate.ps1
Confirm: Your terminal prompt should start with (venv).
Install Required Python Libraries:
pip install fastapi uvicorn pandas numpy scikit-learn prophet matplotlib seaborn holidays joblib
3. Frontend Setup (Node.js & React)
Open a NEW VS Code Terminal (Terminal > New Terminal). This will be your Frontend Terminal.
Navigate to the frontend directory:
cd frontend
Create the React App Structure (IF YOUR frontend FOLDER IS EMPTY):
If your frontend folder is not already filled with React project files (like public/, src/, package.json), run:
npx create-react-app .
Wait: This takes several minutes.
Install Frontend Libraries:
npm install chart.js react-chartjs-2
4. Data Acquisition
EV Sales Data: Ensure EV_Sales_India_Statewise_AllYears.csv.csv is in your data/ folder.
CPI Data: Ensure All India Consumer Price Index.csv is in your data/ folder.
5. Copy & Paste Project Code (Ensure Latest Versions)
Important: To ensure all features and fixes are applied, you must replace the entire content of these files with the latest versions.
backend/data_processing.py: Copy the code block provided in Phase 16, Step 1 (or the last version where CPI integration was successful).
Then Paste and Save.
backend/model_trainer.py: Copy the code block provided in Phase 16, Step 3 (or the last version that trains models with CPI regressors).
Then Paste and Save.
backend/main.py: Copy the code block provided in Phase 11, Step 4 (the version that loads metrics, loads all category models, and uses CPI for future predictions).
Then Paste and Save.
frontend/src/index.css: Copy the code block provided in Phase 23, Step 1.
Then Paste and Save.
frontend/src/App.css: Copy the code block provided in Phase 25, Step 1 (the version for full width, impressive UI, and refined input section).
Then Paste and Save.
frontend/src/App.js: Copy the code block provided in Phase 23, Step 1 (the version with description, historical data, and footer).
Then Paste and Save.
6. Generate Processed Data & Train Models (Execute in Order)
Ensure your Backend Terminal is active (backend directory, (venv) active).
Run data processing (integrates CPI):
python data_processing.py
Verify: After it finishes, check your data/ folder for india_monthly_ev_sales_with_cpi.csv.
Run model training (trains with CPI regressor):
python model_trainer.py
Verify: Check your model/ folder for prophet_ev_sales_model_*.pkl files and model_performance_metrics.json.
7. Run Backend & Frontend Servers
Ensure your Backend Terminal is running (backend directory, (venv) active).
uvicorn main:app --reload
Confirm: Look for messages like Application startup complete. and confirmation of model/metrics loading (including CPI).
Ensure your Frontend Terminal is running (frontend directory).
npm start
Confirm: Your browser opens to http://localhost:3000.
8. Test the Full Application
Open your browser to: http://localhost:3000
Observe the impressive new design, full-page coverage, and the project description in the header.
Enter the desired number of months in the input field.
Click "Get Prediction."
Observe the predicted sales, estimated charging demand, category breakdown, and charts (now showing historical data).
Scroll down to see the "Model Performance Metrics" section and the new footer.
