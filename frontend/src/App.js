
// frontend/src/App.js (Previous Version - NO WHAT-IF SCENARIOS)
import React, { useState, useEffect } from 'react';
import './App.css';
import { Line, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
);

function App() {
  const [futureMonths, setFutureMonths] = useState(12);
  // REMOVED STATES for What-If multipliers
  // const [multiplier2W, setMultiplier2W] = useState(1.0);
  // ... and so on


  const [predictions, setPredictions] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [chartDataSales, setChartDataSales] = useState(null);
  const [chartDataDemand, setChartDataDemand] = useState(null);
  const [chartDataCategoryDemand, setChartDataCategoryDemand] = useState(null);
  const [modelMetrics, setModelMetrics] = useState(null);
  const [metricsLoading, setMetricsLoading] = useState(true);
  const [metricsError, setErrorMetrics] = useState(null);
  const [showMetrics, setShowMetrics] = useState(false);


  const handleInputChange = (event) => {
    const value = event.target.value;
    setFutureMonths(value === '' ? '' : Math.max(1, parseInt(value) || 1));
  };

  // REMOVED HANDLERS for multiplier inputs
  // const handleMultiplierChange = (setter) => (event) => { ... };


  const getPredictions = async () => {
    if (!futureMonths || parseInt(futureMonths) < 1) {
        setError("Please enter a valid number of months (at least 1).");
        setPredictions(null);
        return;
    }

    setLoading(true);
    setError(null);
    setPredictions(null);
    setChartDataSales(null);
    setChartDataDemand(null);
    setChartDataCategoryDemand(null);

    try {
      const response = await fetch('http://127.0.0.1:8000/predict_ev_charging_demand', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          future_months: parseInt(futureMonths),
          // REMOVED: Multipliers from here
        }),
      });

      if (!response.ok) {
        let errorDetail = 'Failed to fetch predictions';
        try {
            const errorData = await response.json();
            errorDetail = errorData.detail || errorData.message || errorDetail;
        } catch (jsonError) {
            errorDetail = `Server error: ${response.status} ${response.statusText}`;
        }
        throw new Error(errorDetail);
      }

      const data = await response.json();
      setPredictions(data);
      
    } catch (err) {
      setError(err.message);
      console.error("Error fetching predictions:", err);
    } finally {
      setLoading(false);
    }
  };

  // Effect to fetch model metrics on component mount
  useEffect(() => {
    const fetchMetrics = async () => {
      setMetricsLoading(true);
      setErrorMetrics(null);
      try {
        const response = await fetch('http://127.0.0.1:8000/model_metrics');
        if (!response.ok) {
          let errorDetail = 'Failed to fetch model metrics';
          try {
            const errorData = await response.json();
            errorDetail = errorData.detail || errorData.message || errorDetail;
          } catch (jsonError) {
            errorDetail = `Server error: ${response.status} ${response.statusText}`;
          }
          throw new Error(errorDetail);
        }
        const data = await response.json();
        setModelMetrics(data);
      } catch (err) {
        setErrorMetrics(err.message);
        console.error("Error fetching model metrics:", err);
      } finally {
        setMetricsLoading(false);
      }
    };

    fetchMetrics();
  }, []); // Empty dependency array means this runs once on mount

  // Effect to prepare chart data whenever predictions change
  useEffect(() => {
    if (predictions && predictions.length > 0) {
      const labels = predictions.map(p => p.date.substring(0, 7)); // Get YYYY-MM
      const totalSales = predictions.map(p => p.total_predicted_sales);
      const totalDemand = predictions.map(p => p.total_predicted_charging_demand_kwh);
      const lowerSales = predictions.map(p => p.lower_bound_total_sales);
      const upperSales = predictions.map(p => p.upper_bound_total_sales);

      // Sales Chart Data
      setChartDataSales({
        labels,
        datasets: [
          {
            label: 'Predicted Sales',
            data: totalSales,
            borderColor: 'rgb(75, 192, 192)',
            backgroundColor: 'rgba(75, 192, 192, 0.5)',
            tension: 0.1,
            fill: false,
          },
          {
            label: 'Lower Bound',
            data: lowerSales,
            borderColor: 'rgb(255, 99, 132)',
            backgroundColor: 'rgba(255, 99, 132, 0.2)',
            borderDash: [5, 5],
            tension: 0.1,
            pointRadius: 0,
            fill: false,
          },
          {
            label: 'Upper Bound',
            data: upperSales,
            borderColor: 'rgb(53, 162, 235)',
            backgroundColor: 'rgba(53, 162, 235, 0.2)',
            borderDash: [5, 5],
            tension: 0.1,
            pointRadius: 0,
            fill: false,
          },
        ],
      });

      // Demand Chart Data
      setChartDataDemand({
        labels,
        datasets: [
          {
            label: 'Estimated Charging Demand (kWh)',
            data: totalDemand,
            borderColor: 'rgb(153, 102, 255)',
            backgroundColor: 'rgba(153, 102, 255, 0.5)',
            tension: 0.1,
            fill: false,
          },
        ],
      });

      // Category-wise Demand (Bar Chart) - for the last predicted month
      if (predictions.length > 0) {
        const lastMonthPred = predictions[predictions.length - 1];
        const categoryLabels = lastMonthPred.category_breakdown.map(cb => cb.category);
        const categoryDemandData = lastMonthPred.category_breakdown.map(cb => cb.predicted_charging_demand_kwh);

        setChartDataCategoryDemand({
            labels: categoryLabels,
            datasets: [{
                label: `Est. Charging Demand (kWh) - ${lastMonthPred.date.substring(0, 7)}`,
                data: categoryDemandData,
                backgroundColor: [
                    'rgba(255, 99, 132, 0.6)',
                    'rgba(54, 162, 235, 0.6)',
                    'rgba(255, 206, 86, 0.6)',
                    'rgba(75, 192, 192, 0.6)',
                    'rgba(153, 102, 255, 0.6)',
                ],
                borderColor: [
                    'rgba(255, 99, 132, 1)',
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(153, 102, 255, 1)',
                ],
                borderWidth: 1,
            }],
        });
      }


    }
  }, [predictions]); // Re-run this effect whenever predictions change

  const chartOptionsCommon = { // Common options for line charts
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
      tooltip: {
        mode: 'index',
        intersect: false,
      },
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Month',
          font: { size: 14 },
          color: '#495057'
        },
      },
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'Value',
          font: { size: 14 },
          color: '#495057'
        },
      },
    },
  };

  const chartOptionsSales = {
    ...chartOptionsCommon,
    plugins: {
      ...chartOptionsCommon.plugins,
      title: {
        display: true,
        text: 'Predicted Total EV Sales Over Time',
        font: { size: 18, weight: 'bold' },
        color: '#343a40'
      },
    },
    scales: {
      ...chartOptionsCommon.scales,
      y: {
        ...chartOptionsCommon.scales.y,
        title: {
          display: true,
          text: 'Number of Vehicles',
          font: { size: 14 },
          color: '#495057'
        },
      },
    },
  };

  const chartOptionsDemand = {
    ...chartOptionsCommon,
    plugins: {
      ...chartOptionsCommon.plugins,
      title: {
        display: true,
        text: 'Estimated Total EV Charging Demand (kWh) Over Time',
        font: { size: 18, weight: 'bold' },
        color: '#343a40'
      },
    },
    scales: {
      ...chartOptionsCommon.scales,
      y: {
        ...chartOptionsCommon.scales.y,
        title: {
          display: true,
          text: 'Energy Demand (kWh)',
          font: { size: 14 },
          color: '#495057'
        },
      },
    },
  };

  const chartOptionsCategoryDemand = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Category-wise Charging Demand for Last Predicted Month',
        font: { size: 18, weight: 'bold' },
        color: '#343a40'
      },
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Vehicle Category',
          font: { size: 14 },
          color: '#495057'
        },
      },
      y: {
        title: {
          display: true,
          text: 'Energy Demand (kWh)',
          font: { size: 14 },
          color: '#495057'
        },
        beginAtZero: true,
      },
    },
  };


  return (
    <div className="App fade-in">
      <header className="App-header">
        <h1>India EV Sales & Charging Demand Prediction</h1>
        <p>Forecasts for a Sustainable Future</p>
      </header>
      <main>
        <div className="input-group">
          <label htmlFor="futureMonths">Predict for how many months?</label>
          <div className="input-controls">
            <input
              type="number"
              id="futureMonths"
              value={futureMonths}
              onChange={handleInputChange}
              min="1"
              aria-label="Number of months to predict"
            />
            <button onClick={getPredictions} disabled={loading}>
              {loading ? 'Predicting...' : 'Get Prediction'}
            </button>
          </div>
        </div>

        {/* REMOVED: Multiplier Inputs for What-If Scenarios */}


        {error && <p className="error-message fade-in">Error: {error}</p>}
        {loading && <p className="loading-message fade-in">Loading predictions...</p>}

        {/* Prediction Results Section */}
        {predictions && predictions.length > 0 && (
          <div className="prediction-container fade-in">
            <h2>Prediction Results:</h2>
            {/* Charts */}
            {chartDataSales && (
                <div className="chart-section fade-in">
                    <Line options={chartOptionsSales} data={chartDataSales} />
                </div>
            )}
            {chartDataDemand && (
                <div className="chart-section fade-in">
                    <Line options={chartOptionsDemand} data={chartDataDemand} />
                </div>
            )}
            {chartDataCategoryDemand && (
                <div className="chart-section fade-in">
                    <Bar options={chartOptionsCategoryDemand} data={chartDataCategoryDemand} />
                </div>
            )}

            {/* Textual summary */}
            <h3>Detailed Forecast:</h3>
            <ul className="prediction-list">
              {predictions.map((prediction, index) => (
                <li key={index} className="prediction-item">
                  <div className="main-prediction-info">
                    <span><strong>Date:</strong> {prediction.date}</span>
                    <span><strong>Total Sales:</strong> {prediction.total_predicted_sales.toLocaleString()}</span>
                    <span><strong>Est. Demand:</strong> {prediction.total_predicted_charging_demand_kwh.toLocaleString()} kWh</span>
                    <span className="bounds">
                        (Sales Range: {prediction.lower_bound_total_sales.toLocaleString()} - {prediction.upper_bound_total_sales.toLocaleString()})
                    </span>
                  </div>
                  <div className="category-breakdown">
                    <h4>Category Breakdown:</h4>
                    <ul>
                      {prediction.category_breakdown.map((cat_pred, cat_idx) => (
                        <li key={cat_idx}>
                          <strong>{cat_pred.category}:</strong> Sales {cat_pred.predicted_sales.toLocaleString()}, Demand {cat_pred.predicted_charging_demand_kwh.toLocaleString()} kWh
                        </li>
                      ))}
                    </ul>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}

        {predictions && predictions.length === 0 && !loading && !error && (
          <p className="fade-in">No predictions found for the specified period.</p>
        )}

        {/* Model Performance Metrics Section - at the end of <main> */}
        <div className="model-metrics-section fade-in">
            <h2 onClick={() => setShowMetrics(!showMetrics)} style={{ cursor: 'pointer' }}>
                Model Performance Metrics {showMetrics ? '▲' : '▼'}
            </h2>
            {metricsLoading && <p className="loading-message">Loading metrics...</p>}
            {metricsError && <p className="error-message">Error loading metrics: {metricsError}</p>}

            {/* Conditionally render content based on showMetrics state */}
            {showMetrics && modelMetrics && Array.isArray(modelMetrics) && modelMetrics.length > 0 && (
                <div className="metrics-grid">
                    {modelMetrics.map((metric, index) => (
                        <div key={index} className="metric-card fade-in">
                            <h3>{metric.category} Model</h3>
                            {metric.status ? (
                                <p>Status: {metric.status}</p>
                            ) : (
                                <>
                                    <p><strong>MAE:</strong> {metric.mae !== "N/A" ? metric.mae.toFixed(2) : "N/A"}</p>
                                    <p><strong>RMSE:</strong> {metric.rmse !== "N/A" ? metric.rmse.toFixed(2) : "N/A"}</p>
                                    <p><strong>MAPE:</strong> {metric.mape !== "N/A" ? (metric.mape * 100).toFixed(2) + '%' : "N/A"}</p>
                                    {metric.horizon && <p>Horizon: {metric.horizon}</p>}
                                </>
                            )}
                        </div>
                    ))}
                </div>
            )}
            {showMetrics && modelMetrics && Array.isArray(modelMetrics) && modelMetrics.length === 0 && !metricsLoading && !metricsError && (
                <p>No model performance metrics available.</p>
            )}
        </div>

      </main>
    </div>
  );
}

export default App;