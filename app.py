import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.optimize import minimize_scalar
from pricing.black_scholes import black_scholes_price
from pricing.greeks import black_scholes_greeks

# ───────────────────  Page config & CSS  ────────────────────────────────
st.set_page_config(page_title="Real Options Analyser", layout="wide")
st.markdown(
    """
    <style>
      .card{
        background:#ffffff;
        padding:1.25rem 1.5rem;
        border-radius:10px;
        box-shadow:0 2px 6px rgba(0,0,0,.05);
        margin-bottom:1.5rem;
      }
      div[data-testid="metric-container"]{margin:0.4rem 0;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ───────────────────  Sidebar controls  ─────────────────────────────────
with st.sidebar:
    st.header("🔧 Controls")
    ticker = st.text_input("Ticker", "AAPL").upper()
    opt_side = st.radio("Option Side", ["Call", "Put"])
    if not ticker:
        st.stop()

# ───────────────────  Header  ───────────────────────────────────────────
st.title("📊 Realtime Options Analyser")

try:
    # ---------------- Company & price history --------------------------
    stock = yf.Ticker(ticker)
    info = stock.info
    hist = stock.history(period="6mo")
    if hist.empty:
        st.error("No historical data found for this ticker.")
        st.stop()

    st.markdown(f"### 🏢 {info.get('shortName', ticker)}")
    if info.get("longBusinessSummary"):
        st.markdown(info["longBusinessSummary"])

    # ---------------- Hero metrics -------------------------------------
    spot = hist["Close"].iloc[-1]
    hist_vol = np.std(np.log(hist["Close"] / hist["Close"].shift(1)).dropna()) * np.sqrt(252)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Spot Price", f"${spot:,.2f}")
        st.caption("This is the latest traded price of the stock.")
    with c2:
        st.metric("6-Month Hist. Vol", f"{hist_vol:.1%}")
        st.caption("Historical volatility measures how much the stock has moved in the last six months.")
    with c3:
        iv_metric = st.empty()
        st.caption("At-the-money implied volatility will appear here once you choose a strike.")

    # ---------------- Option chain & IV estimation ---------------------
    expiry = st.sidebar.selectbox("Expiration Date", stock.options)
    option_type = "call" if opt_side == "Call" else "put"

    chain = stock.option_chain(expiry)
    df = (chain.calls if option_type == "call" else chain.puts).copy()
    df["mid"] = (df["bid"] + df["ask"]) / 2
    df = df.dropna(subset=["mid"])

    T = ((np.datetime64(expiry) - np.datetime64("today")) / np.timedelta64(1, "D")) / 365.0
    r = 0.05

    def iv_objective(sig, S, K, T, r, mkt, typ):
        return abs(black_scholes_price(S, K, T, r, sig, typ) - mkt)

    for i, row in df.iterrows():
        res = minimize_scalar(
            iv_objective, bounds=(0.01, 2), method="bounded",
            args=(spot, row["strike"], T, r, row["mid"], option_type)
        )
        if res.success:
            df.loc[i, "impliedVol"] = res.x
            df.loc[i, "modelPrice"] = black_scholes_price(spot, row["strike"], T, r, res.x, option_type)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### Option-Chain Snapshot")
    st.dataframe(df[["strike", "mid", "impliedVol", "modelPrice"]].round(4))
    st.markdown('</div>', unsafe_allow_html=True)

    # ---------------- Strike selection & ATM-IV update ------------------
    atm_strike = df.iloc[(df["strike"] - spot).abs().argsort()[:1]]["strike"].values[0]
    strike = st.sidebar.selectbox("Strike", df["strike"], index=df["strike"].tolist().index(atm_strike))
    sigma = df.loc[df["strike"] == strike, "impliedVol"].values[0]
    iv_metric.metric("ATM Implied Vol", f"{sigma:.1%}")

    # ---------------- Greeks card --------------------------------------
    greeks = black_scholes_greeks(spot, strike, max(T, 1e-5), r, max(sigma, 1e-5), option_type)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### 📐 Greeks")
    gcols = st.columns(5)
    for (name, value), col in zip(greeks.items(), gcols):
        col.metric(name, f"{value:.3f}")
    st.markdown(
        """
**Delta** tells us how much the option price changes when the stock moves one dollar.  
**Gamma** measures how quickly Delta itself will change as the stock moves.  
**Vega** shows the dollar impact of a one-percentage-point move in implied volatility.  
**Theta** expresses the dollar value the option loses with the passing of one day, while **Rho** shows the effect of a one-percentage-point shift in interest rates.
""",
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # ---------------- Interpretation & scenarios -----------------------
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### 🧠 Interpretation & Scenario Analysis")

    direction = "bullish" if option_type == "call" else "bearish"
    itm_state = "in-the-money" if (
        option_type == "call" and spot > strike) or (
        option_type == "put" and spot < strike) else "out-of-the-money"
    st.write(
        f"The selected option is a **{direction} {option_type}** that is currently **{itm_state}**. "
        "Because of its position relative to the strike, Delta and Gamma indicate how sensitively it will respond to price moves."
    )

    premium = df.loc[df["strike"] == strike, "mid"].values[0]
    breakeven = strike + premium if option_type == "call" else strike - premium
    st.write(
        f"The break-even price at expiration is **${breakeven:,.2f}**. "
        "Beyond this level the option starts to realise intrinsic profit."
    )

    st.write(
        "From the scenario below you can see how movement in the stock price and changes in implied volatility "
        "translate into approximate dollar changes in the option’s value."
    )

    delta_effect = greeks["Delta"] * 5
    vega_effect = greeks["Vega"] * 0.05
    st.info(
        f"If the stock moves up or down by $5, the option value is expected to change by roughly **{delta_effect:+.2f} dollars**.  "
        f"If implied volatility rises or falls by 5 percentage-points, the option value should move by approximately **{vega_effect:+.2f} dollars**."
    )

    st.markdown(
        """
**For buyers** the maximum loss is limited to the premium paid, while the upside can be substantial if the stock makes a decisive move and volatility expands.  
**For sellers** the premium is collected up-front, but large adverse price moves or volatility spikes can create theoretically unlimited risk.
"""
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # ---------------- Helper ranges for plots ---------------------------
    S_range = np.linspace(spot * 0.5, spot * 1.5, 100)
    time_range = np.linspace(0.01, T, 100)

    # ---------------- Core visualisations in tabs -----------------------
    tab_price, tab_delta, tab_theta = st.tabs(["Price curve", "Delta curve", "Theta decay"])

    # ----- Price curve --------------------------------------------------
    with tab_price:
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("##### Option Price vs. Stock Price")
            price_curve = [black_scholes_price(S, strike, T, r, sigma, option_type) for S in S_range]
            fig_price = go.Figure(go.Scatter(x=S_range, y=price_curve, line=dict(color="#1f77b4")))
            fig_price.update_layout(template="plotly_white", xaxis_title="Stock Price", yaxis_title="Option Price")
            st.plotly_chart(fig_price, use_container_width=True)
            st.caption(
                "The blue line plots theoretical option value against a wide range of stock prices.  "
                "The sharp bend at the strike marks the point where intrinsic value begins to outweigh time value.  "
                "The left-hand plateau shows how deep-out-of-the-money options hold only time value.  "
                "The slope at any point approximates Delta, while the curvature reflects Gamma."
            )
            st.markdown('</div>', unsafe_allow_html=True)

    # ----- Delta curve --------------------------------------------------
    with tab_delta:
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("##### Delta vs. Stock Price")
            delta_curve = [
                black_scholes_greeks(S, strike, max(T, 1e-5), r, max(sigma, 1e-5), option_type)["Delta"]
                for S in S_range
            ]
            fig_delta = go.Figure(go.Scatter(x=S_range, y=delta_curve, line=dict(color="#2ca02c")))
            fig_delta.update_layout(template="plotly_white", xaxis_title="Stock Price", yaxis_title="Delta")
            st.plotly_chart(fig_delta, use_container_width=True)
            st.caption(
                "This curve starts near zero when the option is far out-of-the-money and rises towards ±1 as it moves in-the-money.  "
                "The steepest segment, which sits near the strike, corresponds to the region of highest Gamma.  "
                "When Delta is about 0.50 the option has roughly a fifty-fifty chance of expiring in-the-money.  "
                "Deep-in-the-money options with a Delta near one mimic stock exposure almost one-for-one."
            )
            st.markdown('</div>', unsafe_allow_html=True)

    # ----- Theta decay ---------------------------------------------------
    with tab_theta:
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("##### Theta Decay Over Time")
            theta_curve = [
                black_scholes_greeks(spot, strike, t, r, max(sigma, 1e-5), option_type)["Theta"]
                for t in time_range
            ]
            fig_theta = go.Figure(go.Scatter(x=time_range, y=theta_curve, line=dict(color="#d62728")))
            fig_theta.update_layout(template="plotly_white", xaxis_title="Years to Expiry", yaxis_title="Theta")
            st.plotly_chart(fig_theta, use_container_width=True)
            st.caption(
                "Theta quantifies the option’s daily time decay.  "
                "Notice how the curve slopes gently for long-dated options and plunges as expiration draws close.  "
                "Options that are at-the-money decay fastest because their time value is highest.  "
                "The total extrinsic value yet to be lost is roughly the area under this curve."
            )
            st.markdown('</div>', unsafe_allow_html=True)

    # ---------------- Supplementary cards in three columns --------------
    col_bar, col_mc, col_iv = st.columns(3)

    # --- Nearby-strike Greeks bar chart
    with col_bar:
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("##### Nearby-Strike Greeks")
            near = df[(df["strike"] >= strike * 0.9) & (df["strike"] <= strike * 1.1)]
            rows = []
            for _, rw in near.iterrows():
                if rw["impliedVol"]:
                    g = black_scholes_greeks(
                        spot, rw["strike"], max(T, 1e-5), r, max(rw["impliedVol"], 1e-5), option_type
                    )
                    rows.append({"strike": rw["strike"], **{k: g[k] for k in ["Delta", "Vega", "Theta"]}})
            if rows:
                df_g = pd.DataFrame(rows)
                fig_bar = go.Figure()
                for gk in ["Delta", "Vega", "Theta"]:
                    fig_bar.add_trace(go.Bar(x=df_g["strike"], y=df_g[gk], name=gk))
                fig_bar.update_layout(template="plotly_white", barmode="group")
                st.plotly_chart(fig_bar, use_container_width=True)
            st.caption(
                "The grouped bars compare Delta, Vega and Theta for strikes within ten percent of the one you selected.  "
                "You can quickly see which alternatives give more volatility exposure or less time decay.  "
                "Higher Vega bars suit volatility trades, while lower Theta bars appeal to long-term holders.  "
                "Such comparisons help you fine-tune multi-leg strategies."
            )
            st.markdown('</div>', unsafe_allow_html=True)

    # --- Monte-Carlo histogram
    with col_mc:
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("##### Monte Carlo Simulation")
            np.random.seed(42)
            ST = spot * np.exp(
                (r - 0.5 * sigma ** 2) * T + sigma * np.sqrt(T) * np.random.normal(size=1000)
            )
            fig_mc = go.Figure(go.Histogram(x=ST, nbinsx=40, marker_color="#1f77b4", opacity=0.75))
            fig_mc.update_layout(template="plotly_white", xaxis_title="Terminal Stock Price", yaxis_title="Frequency")
            st.plotly_chart(fig_mc, use_container_width=True)
            st.caption(
                "The histogram shows the distribution of one thousand simulated terminal prices under the Black-Scholes assumptions.  "
                "The width of the spread reflects the implied volatility you selected.  "
                "Prices beyond the break-even point hint at profitable outcomes for option buyers.  "
                "Conversely, the frequency of extreme outcomes illustrates tail risk for sellers."
            )
            st.markdown('</div>', unsafe_allow_html=True)

    # --- Implied-volatility curve
    with col_iv:
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("##### Implied Volatility Curve")
            iv_df = df.dropna(subset=["impliedVol"])
            fig_iv = go.Figure(go.Scatter(
                x=iv_df["strike"], y=iv_df["impliedVol"],
                mode="lines+markers", line=dict(color="#9467bd")
            ))
            fig_iv.update_layout(template="plotly_white", xaxis_title="Strike Price", yaxis_title="Implied Volatility")
            st.plotly_chart(fig_iv, use_container_width=True)
            st.caption(
                "The IV curve reveals whether the market prices higher volatility in out-of-the-money puts or calls.  "
                "A pronounced skew with elevated put volatility suggests demand for downside protection.  "
                "Comparing these IV levels with historical volatility highlights potentially rich or cheap strikes.  "
                "Traders often exploit such skews through risk-reversal or vertical-spread strategies."
            )
            st.markdown('</div>', unsafe_allow_html=True)

except Exception as e:
    st.error(f"⚠️ {e}")
