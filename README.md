# 📊 Real-World Options Analyser

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/<your-user>/option-pricing-streamlit/main/app.py)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

This interactive Streamlit dashboard allows you to analyse real-world options data for any stock symbol.  
It calculates Black-Scholes option prices, Greeks, implied volatility, and offers intuitive visualisations to help you understand market sensitivity and time decay.

---

## ✨ Features

- **Live Option Chain**: Pulls call/put data from Yahoo Finance.
- **Implied Volatility Estimation**: Numerically solved using Brent's method.
- **Black-Scholes Greeks**: Delta, Gamma, Vega, Theta, Rho.
- **Interpretations & Scenarios**: Plain-language explanations for each Greek and “what-if” stock/volatility changes.
- **Visualizations**:
  - Option Price vs. Stock Price Curve
  - Delta Sensitivity Curve
  - Theta Decay Curve
  - Nearby Strike Greeks (Bar Chart)
  - Monte Carlo Simulation of Terminal Prices
  - Implied Volatility Smile
- **Responsive Layout**: Light UI with containerised chart sections and concise annotations.

---

## 🧭 How to Use the App

1. Enter a **stock ticker** (e.g., `AAPL`, `MSFT`).
2. Select an **expiration date** and **option type** (Call/Put).
3. View:
   - Current **spot price**
   - **Historical volatility**
   - **Implied volatility** at-the-money
4. Choose a **strike price** to:
   - Calculate **Greeks**
   - Read **interpretations** and scenario impact
5. Explore each tabbed chart to see option pricing behavior and volatility dynamics.
6. Scroll down for supplemental visuals:
   - Bar chart comparing Greeks across strikes
   - Monte Carlo histogram
   - IV smile curve

---

## 📁 Project Structure

```text
option-pricing-streamlit/
├── app.py                 # Main Streamlit app logic and layout
├── pricing/               # Modular code for pricing and Greeks calculations
│   ├── black_scholes.py   # Black-Scholes pricing function
│   └── greeks.py          # Functions to compute Delta, Gamma, Vega, Theta, Rho
├── docs/                  # Assets like screenshots or GIFs
│   └── screenshot.png     # App preview image
├── requirements.txt       # Python package dependencies
└── README.md              # Project documentation
```
---

## 🖥️ Live Demo

> Heres a short live demo of this page.

![Demo of the app](docs/demo.gif)

---

## ⚙️ Tech Stack

- **Python 3.9+**
- **Streamlit** – app framework
- **yfinance** – fetches market/option data
- **NumPy, SciPy, Pandas** – analytics and numerical modeling
- **Plotly** – interactive visualisations

---

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/<your-user>/option-pricing-streamlit.git
cd option-pricing-streamlit

# Optional: Create a virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install required libraries
pip install -r requirements.txt

# Run the app
streamlit run app.py

```

## 📄 License
MIT License — see LICENSE for full details.
