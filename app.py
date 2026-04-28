import io
from itertools import combinations

import altair as alt
import pandas as pd
import streamlit as st

from data_quality import run_checks


st.set_page_config(page_title="Sales Analytics MVP", layout="wide")


def safe_div(numerator, denominator):
    if denominator is None or denominator == 0:
        return 0
    return numerator / denominator


def check_empty_data(df, context=""):
    """Helper to check if dataframe is empty and show user message"""
    if df.empty:
        st.warning(f"⚠️ No data available{f' for {context}' if context else ''}. Try adjusting filters.")
        return True
    return False


@st.cache_data
def load_data(path="master_sales_analysis.csv"):
    return pd.read_csv(path, parse_dates=["transaction_date", "delivery_date"], low_memory=False)


def filter_df(df):
    if df.empty:
        return df

    min_date = df["transaction_date"].min().date()
    max_date = df["transaction_date"].max().date()
    date_range = st.sidebar.date_input("Date range", value=[min_date, max_date])
    if isinstance(date_range, list) and len(date_range) == 2:
        start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        df = df[(df["transaction_date"] >= start) & (df["transaction_date"] <= end)]

    categories = sorted(df["category_name"].dropna().unique()) if "category_name" in df.columns else []
    sel_categories = st.sidebar.multiselect("Category", options=categories)
    if sel_categories:
        df = df[df["category_name"].isin(sel_categories)]

    products = sorted(df["product_code"].dropna().unique()) if "product_code" in df.columns else []
    sel_products = st.sidebar.multiselect("Product", options=products, max_selections=30)
    if sel_products:
        df = df[df["product_code"].isin(sel_products)]

    channels = sorted(df["customer_channel"].dropna().unique()) if "customer_channel" in df.columns else []
    sel_channels = st.sidebar.multiselect("Customer Channel", options=channels)
    if sel_channels:
        df = df[df["customer_channel"].isin(sel_channels)]

    areas = sorted(df["customer_city_prov"].dropna().unique()) if "customer_city_prov" in df.columns else []
    sel_areas = st.sidebar.multiselect("Area", options=areas)
    if sel_areas:
        df = df[df["customer_city_prov"].isin(sel_areas)]

    salesmen = sorted(df["salesman_name"].dropna().unique()) if "salesman_name" in df.columns else []
    sel_sales = st.sidebar.multiselect("Salesman", options=salesmen)
    if sel_sales:
        df = df[df["salesman_name"].isin(sel_sales)]

    return df


def build_product_summary(df):
    by_prod = (
        df.groupby(["product_code", "product_name", "category_name"], dropna=False)
        .agg(
            total_revenue=("total_revenue", "sum"),
            quantity=("quantity", "sum"),
            gross_profit=("gross_profit", "sum"),
        )
        .reset_index()
    )
    by_prod["margin_percent"] = by_prod.apply(
        lambda r: safe_div(r["gross_profit"], r["total_revenue"]) * 100, axis=1
    )
    return by_prod


def build_customer_summary(df):
    return (
        df.groupby(["customer_code", "customer_name", "customer_channel"], dropna=False)
        .agg(
            total_revenue=("total_revenue", "sum"),
            quantity=("quantity", "sum"),
            gross_profit=("gross_profit", "sum"),
        )
        .reset_index()
    )


def overview_tab(df):
    st.header("Overview")
    col1, col2, col3, col4 = st.columns(4)
    total_revenue = df["total_revenue"].sum()
    total_qty = df["quantity"].sum()
    invoices = df["bill_no"].nunique()
    aov = safe_div(total_revenue, invoices)
    gross_profit = df["gross_profit"].sum()

    col1.metric("Total Revenue", f"{total_revenue:,.0f}")
    col2.metric("Quantity Sold", f"{total_qty:,.0f}")
    col3.metric("AOV", f"{aov:,.2f}")
    col4.metric("Gross Profit", f"{gross_profit:,.0f}")

    st.subheader("Revenue Trend")
    rev_ts = df.set_index("transaction_date").resample("W")["total_revenue"].sum()
    st.line_chart(rev_ts)

    st.subheader("Top Categories by Revenue")
    if "category_name" in df.columns:
        cat = df.groupby("category_name", dropna=False).agg(revenue=("total_revenue", "sum")).reset_index()
        cat = cat.sort_values("revenue", ascending=False).head(10)
        chart = alt.Chart(cat).mark_bar().encode(
            x=alt.X("revenue:Q", title="Revenue"),
            y=alt.Y("category_name:N", sort="-x", title="Category"),
        )
        st.altair_chart(chart)

    st.subheader("Margin % Distribution")
    if "margin_percent" in df.columns:
        hist = alt.Chart(df.dropna(subset=["margin_percent"])).mark_bar().encode(
            alt.X("margin_percent:Q", bin=alt.Bin(maxbins=30), title="Margin %"),
            y="count()",
        )
        st.altair_chart(hist)

    st.subheader("Payment Method Distribution")
    if "payment_type" in df.columns:
        payment_dist = df["payment_type"].value_counts().reset_index()
        payment_dist.columns = ["payment_type", "count"]
        pie_chart = alt.Chart(payment_dist).mark_arc().encode(
            theta="count:Q",
            color="payment_type:N",
            tooltip=["payment_type", "count"],
        )
        st.altair_chart(pie_chart)

    st.subheader("Reconciliation & Flagged Issues")
    with st.expander("KPI reconciliation"):
        st.write(
            {
                "total_revenue": float(total_revenue),
                "total_quantity": float(total_qty),
                "gross_profit": float(gross_profit),
                "invoices": int(invoices),
            }
        )

    rpt, issues = run_checks()
    st.write("Data quality summary (master file):")
    st.json(rpt)

    if rpt['negative_gross_profit'] > 0:
        st.warning(f"⚠️ **Data Quality Note:** {rpt['negative_gross_profit']} transaction(s) have negative margins (below base_price). These may be promotional pricing, discounts, or require review.")
        with st.expander("View negative margin transactions"):
            if issues.get('negative_gross_profit_sample'):
                neg_df = pd.DataFrame(issues['negative_gross_profit_sample'])
                st.dataframe(neg_df[['bill_no', 'product_code', 'product_name', 'selling_price', 'base_price', 'margin_percent']])

    flagged_rows = []
    if isinstance(issues.get("negative_gross_profit_sample"), list):
        flagged_rows.extend(issues.get("negative_gross_profit_sample"))
    if isinstance(issues.get("base_price_zero_sample"), list):
        flagged_rows.extend(issues.get("base_price_zero_sample"))

    if flagged_rows:
        flagged_df = pd.DataFrame(flagged_rows)
        st.subheader("Sample Flagged Rows")
        st.dataframe(flagged_df.head(50))
        st.download_button(
            "Download flagged issues CSV",
            data=flagged_df.to_csv(index=False),
            file_name="flagged_issues.csv",
        )


def product_tab(df):
    st.header("Product Analysis")
    if check_empty_data(df, "Product Analysis"):
        return
    
    by_prod = build_product_summary(df)
    if check_empty_data(by_prod, "products"):
        return

    negative_margin = by_prod[by_prod["margin_percent"] < 0]
    if not negative_margin.empty:
        st.warning(f"⚠️ **Alert:** {len(negative_margin)} product(s) have negative margins. Check pricing strategy.")
        with st.expander("View products with negative margin"):
            st.dataframe(negative_margin[["product_code", "product_name", "total_revenue", "gross_profit", "margin_percent"]])

    st.subheader("Top Products by Revenue")
    top = by_prod.sort_values("total_revenue", ascending=False).head(20)
    chart = alt.Chart(top).mark_bar().encode(
        x=alt.X("total_revenue:Q", title="Revenue"),
        y=alt.Y("product_name:N", sort="-x", title="Product"),
        color="category_name:N",
        tooltip=["product_code", "product_name", "category_name", "total_revenue", "quantity", "gross_profit"],
    )
    st.altair_chart(chart)

    st.subheader("Margin vs Revenue (Products)")
    scatter = (
        alt.Chart(by_prod.dropna(subset=["margin_percent"]))
        .mark_circle(size=60)
        .encode(
            x=alt.X("total_revenue:Q", title="Revenue"),
            y=alt.Y("margin_percent:Q", title="Margin %"),
            color="category_name:N",
            tooltip=["product_code", "product_name", "total_revenue", "margin_percent", "quantity"],
        )
        .interactive()
    )
    st.altair_chart(scatter)

    st.subheader("Top 50 Products Table")
    st.dataframe(by_prod.sort_values("total_revenue", ascending=False).head(50))
    st.download_button(
        "Download product summary CSV",
        data=by_prod.to_csv(index=False),
        file_name="product_summary.csv",
    )


def customer_tab(df):
    st.header("Customer Analysis")
    if check_empty_data(df, "Customer Analysis"):
        return
    
    by_cust = build_customer_summary(df)
    if check_empty_data(by_cust, "customers"):
        return

    st.subheader("Top Customers by Revenue")
    topc = by_cust.sort_values("total_revenue", ascending=False).head(20)
    chart = alt.Chart(topc).mark_bar().encode(
        x=alt.X("total_revenue:Q", title="Revenue"),
        y=alt.Y("customer_name:N", sort="-x", title="Customer"),
        color="customer_channel:N",
        tooltip=["customer_code", "customer_name", "customer_channel", "total_revenue", "quantity"],
    )
    st.altair_chart(chart)

    st.subheader("Customer Revenue Distribution")
    hist = alt.Chart(by_cust).mark_bar().encode(
        x=alt.X("total_revenue:Q", bin=alt.Bin(maxbins=30), title="Customer Revenue"),
        y="count()",
    )
    st.altair_chart(hist)

    st.subheader("Top 50 Customers Table")
    st.dataframe(by_cust.sort_values("total_revenue", ascending=False).head(50))
    st.download_button(
        "Download customer summary CSV",
        data=by_cust.to_csv(index=False),
        file_name="customer_summary.csv",
    )


def advanced_customer_tab(df):
    st.header("Advanced Customer: RFM, Retention, CLV")
    
    if check_empty_data(df, "Advanced Customer Analysis"):
        return

    st.info("""
    **RFM Scoring Guide:**
    - **R (Recency):** 5 = most recent, 1 = least recent
    - **F (Frequency):** 5 = most frequent, 1 = least frequent  
    - **M (Monetary):** 5 = highest value, 1 = lowest value
    - **RFM Total:** 15 (best) to 3 (worst) — prioritize high scores for retention.
    """)

    customer_base = (
        df.groupby(["customer_code", "customer_name"], dropna=False)
        .agg(
            first_purchase=("transaction_date", "min"),
            last_purchase=("transaction_date", "max"),
            frequency=("bill_no", "nunique"),
            monetary=("total_revenue", "sum"),
            gross_profit=("gross_profit", "sum"),
        )
        .reset_index()
    )

    reference_date = df["transaction_date"].max() + pd.Timedelta(days=1)
    customer_base["recency_days"] = (reference_date - customer_base["last_purchase"]).dt.days

    def score_quantile(series, reverse=False):
        ranked = series.rank(method="first")
        if reverse:
            ranked = (-series).rank(method="first")
        return pd.qcut(ranked, q=5, labels=[1, 2, 3, 4, 5], duplicates="drop").astype(int)

    customer_base["r_score"] = score_quantile(customer_base["recency_days"], reverse=True)
    customer_base["f_score"] = score_quantile(customer_base["frequency"], reverse=False)
    customer_base["m_score"] = score_quantile(customer_base["monetary"], reverse=False)
    customer_base["rfm_score"] = (
        customer_base["r_score"].astype(str)
        + customer_base["f_score"].astype(str)
        + customer_base["m_score"].astype(str)
    )
    customer_base["rfm_total"] = customer_base["r_score"] + customer_base["f_score"] + customer_base["m_score"]

    customer_base["lifespan_months"] = (
        (customer_base["last_purchase"] - customer_base["first_purchase"]).dt.days / 30
    ).clip(lower=1)
    customer_base["aov"] = customer_base["monetary"] / customer_base["frequency"].clip(lower=1)
    customer_base["purchase_frequency_monthly"] = customer_base["frequency"] / customer_base["lifespan_months"]
    customer_base["margin_rate"] = customer_base.apply(
        lambda r: safe_div(r["gross_profit"], r["monetary"]), axis=1
    ).clip(lower=0)
    customer_base["clv_12m"] = (
        customer_base["aov"]
        * customer_base["purchase_frequency_monthly"]
        * customer_base["margin_rate"]
        * 12
    )

    st.subheader("RFM Table")
    st.dataframe(
        customer_base[
            [
                "customer_code",
                "customer_name",
                "recency_days",
                "frequency",
                "monetary",
                "r_score",
                "f_score",
                "m_score",
                "rfm_score",
                "rfm_total",
            ]
        ].sort_values(["rfm_total", "monetary"], ascending=[False, False]).head(200)
    )

    st.subheader("Churn / Retention Snapshot")
    latest_date = df["transaction_date"].max()

    churn_window = st.slider("Days for recent activity window", min_value=7, max_value=60, value=30, step=7)
    prev_window = st.slider("Days for previous window", min_value=14, max_value=120, value=60, step=7)

    recent_start = latest_date - pd.Timedelta(days=churn_window)
    prev_start = latest_date - pd.Timedelta(days=prev_window)

    active_recent = set(df[df["transaction_date"] > recent_start]["customer_code"].dropna().unique())
    active_prev = set(
        df[(df["transaction_date"] > prev_start) & (df["transaction_date"] <= recent_start)]["customer_code"]
        .dropna()
        .unique()
    )

    retained = active_recent.intersection(active_prev)
    churned = active_prev.difference(active_recent)
    new_customers = active_recent.difference(active_prev)

    retention_rate = safe_div(len(retained), len(active_prev)) * 100
    churn_rate = safe_div(len(churned), len(active_prev)) * 100

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Active Prev 30D", len(active_prev))
    c2.metric("Retained", len(retained))
    c3.metric("Churned", len(churned))
    c4.metric("Retention Rate", f"{retention_rate:.2f}%")
    st.caption(f"Churn Rate: {churn_rate:.2f}% | New Customers (recent 30D): {len(new_customers)}")

    st.subheader("Top Customers by CLV (12M Proxy)")
    st.dataframe(
        customer_base[
            ["customer_code", "customer_name", "clv_12m", "aov", "purchase_frequency_monthly", "margin_rate"]
        ]
        .sort_values("clv_12m", ascending=False)
        .head(50)
    )


def forecast_tab(df):
    st.header("Forecasting: Moving Average per Product / Channel")
    
    if check_empty_data(df, "Forecasting"):
        return

    mode = st.radio("Forecast mode", ["Product", "Channel"], horizontal=True)
    forecast_window = st.slider("Moving average window (weeks)", min_value=2, max_value=12, value=4)
    horizon = st.slider("Forecast horizon (weeks)", min_value=2, max_value=12, value=6)

    if mode == "Product":
        values = sorted(df["product_code"].dropna().unique())
        key_col = "product_code"
    else:
        values = sorted(df["customer_channel"].dropna().unique())
        key_col = "customer_channel"

    if not values:
        st.info("No data available for forecasting after filters")
        return

    selected = st.selectbox(f"Select {mode}", values)
    sub = df[df[key_col] == selected].copy()
    ts = sub.set_index("transaction_date").resample("W")["total_revenue"].sum().sort_index()

    if ts.empty:
        st.info("No time series data available")
        return

    history_values = ts.tolist()
    forecasts = []
    for _ in range(horizon):
        window_vals = history_values[-forecast_window:] if len(history_values) >= forecast_window else history_values
        next_val = sum(window_vals) / len(window_vals) if window_vals else 0
        forecasts.append(next_val)
        history_values.append(next_val)

    future_idx = pd.date_range(start=ts.index.max() + pd.Timedelta(weeks=1), periods=horizon, freq="W")
    forecast_df = pd.DataFrame({"transaction_date": future_idx, "forecast_revenue": forecasts})

    actual_df = ts.reset_index().rename(columns={"total_revenue": "value"})
    actual_df["type"] = "actual"
    pred_df = forecast_df.rename(columns={"forecast_revenue": "value"})
    pred_df["type"] = "forecast"
    line_df = pd.concat([actual_df, pred_df], ignore_index=True)

    chart = (
        alt.Chart(line_df)
        .mark_line(point=True)
        .encode(
            x=alt.X("transaction_date:T", title="Week"),
            y=alt.Y("value:Q", title="Revenue"),
            color=alt.Color("type:N", scale=alt.Scale(domain=["actual", "forecast"], range=["#1f77b4", "#d62728"])),
        )
    )
    st.altair_chart(chart)
    st.dataframe(forecast_df)


def market_basket_tab(df):
    st.header("Market Basket Analysis")
    
    if check_empty_data(df, "Market Basket Analysis"):
        return

    baskets = (
        df.groupby("bill_no")["product_code"]
        .apply(lambda s: sorted(set([x for x in s.dropna().tolist() if str(x).strip() != ""])))
        .reset_index(drop=True)
    )
    baskets = baskets[baskets.apply(len) >= 2]

    if baskets.empty:
        st.info("No multi-item baskets found for current filters")
        return

    item_counts = {}
    pair_counts = {}
    for items in baskets:
        for item in items:
            item_counts[item] = item_counts.get(item, 0) + 1
        for a, b in combinations(items, 2):
            pair = tuple(sorted((a, b)))
            pair_counts[pair] = pair_counts.get(pair, 0) + 1

    total_baskets = len(baskets)
    rules = []
    for (a, b), pair_count in pair_counts.items():
        support_ab = pair_count / total_baskets
        support_a = item_counts[a] / total_baskets
        support_b = item_counts[b] / total_baskets

        conf_a_b = safe_div(pair_count, item_counts[a])
        conf_b_a = safe_div(pair_count, item_counts[b])
        lift_a_b = safe_div(conf_a_b, support_b)
        lift_b_a = safe_div(conf_b_a, support_a)

        rules.append(
            {
                "antecedent": a,
                "consequent": b,
                "support": support_ab,
                "confidence": conf_a_b,
                "lift": lift_a_b,
                "pair_count": pair_count,
            }
        )
        rules.append(
            {
                "antecedent": b,
                "consequent": a,
                "support": support_ab,
                "confidence": conf_b_a,
                "lift": lift_b_a,
                "pair_count": pair_count,
            }
        )

    rules_df = pd.DataFrame(rules).sort_values(["lift", "confidence"], ascending=False)
    min_support = st.slider("Minimum support", min_value=0.01, max_value=0.50, value=0.05, step=0.01)
    min_conf = st.slider("Minimum confidence", min_value=0.05, max_value=1.00, value=0.20, step=0.05)

    filtered_rules = rules_df[(rules_df["support"] >= min_support) & (rules_df["confidence"] >= min_conf)]
    st.dataframe(filtered_rules.head(100))
    st.download_button(
        "Download market basket rules CSV",
        data=filtered_rules.to_csv(index=False),
        file_name="market_basket_rules.csv",
    )


def financial_tab(df):
    st.header("Financial Analytics: Aging / DSO / Collection")
    
    if check_empty_data(df, "Financial Analytics"):
        return

    work = df.copy()
    work["payment_type_upper"] = work["payment_type"].astype(str).str.upper()
    work["payment_status_upper"] = work["payment_status"].astype(str).str.upper()

    credit_df = work[work["payment_type_upper"] == "CREDIT"]
    paid_credit = credit_df[credit_df["payment_status_upper"] == "PAID"]
    outstanding = credit_df[credit_df["payment_status_upper"] != "PAID"].copy()

    today = pd.Timestamp.today().normalize()
    outstanding["receivable_age_days"] = (today - outstanding["transaction_date"]).dt.days
    outstanding["aging_bucket"] = pd.cut(
        outstanding["receivable_age_days"],
        bins=[-1, 30, 60, 90, 10000],
        labels=["0-30", "31-60", "61-90", "90+"],
    )

    credit_sales_total = credit_df["total_revenue"].sum()
    collected_credit = paid_credit["total_revenue"].sum()
    outstanding_amt = outstanding["total_revenue"].sum()

    min_date = work["transaction_date"].min()
    max_date = work["transaction_date"].max()
    period_days = max((max_date - min_date).days + 1, 1)
    avg_daily_credit_sales = safe_div(credit_sales_total, period_days)
    dso = safe_div(outstanding_amt, avg_daily_credit_sales)
    collection_efficiency = safe_div(collected_credit, credit_sales_total) * 100

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Outstanding Receivable", f"{outstanding_amt:,.0f}")
    c2.metric("Credit Sales", f"{credit_sales_total:,.0f}")
    c3.metric("Collection Efficiency", f"{collection_efficiency:.2f}%")
    c4.metric("DSO (days)", f"{dso:.2f}")

    st.subheader("Aging Buckets")
    aging = (
        outstanding.groupby("aging_bucket", dropna=False)
        .agg(amount=("total_revenue", "sum"), invoices=("bill_no", "nunique"))
        .reset_index()
    )
    st.dataframe(aging)

    aging_chart = alt.Chart(aging).mark_bar().encode(
        x=alt.X("aging_bucket:N", title="Aging Bucket"),
        y=alt.Y("amount:Q", title="Outstanding Amount"),
        tooltip=["aging_bucket", "amount", "invoices"],
    )
    st.altair_chart(aging_chart)

    st.subheader("Outstanding Receivable Detail")
    detail_cols = [
        "bill_no",
        "transaction_date",
        "customer_code",
        "customer_name",
        "salesman_name",
        "total_revenue",
        "receivable_age_days",
        "aging_bucket",
    ]
    detail_cols = [c for c in detail_cols if c in outstanding.columns]
    st.dataframe(outstanding[detail_cols].sort_values("receivable_age_days", ascending=False).head(300))


def logistics_tab(df):
    st.header("Logistics")
    
    if check_empty_data(df, "Logistics"):
        return
        
    if "delivery_lead_time_days" not in df.columns:
        st.info("No delivery lead time data available")
        return

    lead = df["delivery_lead_time_days"].dropna()
    if len(lead) == 0:
        st.info("No delivery lead time data available")
        return
        
    st.subheader("Delivery Lead Time (days)")
    st.bar_chart(lead.value_counts().sort_index())

    avg_lead = lead.mean()
    median_lead = lead.median()
    c1, c2 = st.columns(2)
    c1.metric("Average Lead Time (days)", f"{avg_lead:.2f}")
    c2.metric("Median Lead Time (days)", f"{median_lead:.2f}")

    delivered = df[df["is_delivered"] == True]
    on_time = delivered[delivered["delivery_lead_time_days"] <= 3]
    on_time_pct = safe_div(len(on_time), len(delivered)) * 100
    st.write({"delivered_count": len(delivered), "on_time_percent": round(on_time_pct, 2)})

    if "delivery_vehicle" in df.columns:
        vehicles = df["delivery_vehicle"].value_counts().head(10).reset_index()
        vehicles.columns = ["delivery_vehicle", "count"]
        chart = alt.Chart(vehicles).mark_bar().encode(
            x="count:Q",
            y=alt.Y("delivery_vehicle:N", sort="-x"),
        )
        st.altair_chart(chart)


def salesman_tab(df):
    st.header("Salesman Performance Dashboard")
    
    if check_empty_data(df, "Salesman Performance"):
        return

    salesman_agg = (
        df.groupby("salesman_name", dropna=False)
        .agg(
            total_revenue=("total_revenue", "sum"),
            quantity=("quantity", "sum"),
            gross_profit=("gross_profit", "sum"),
            invoices=("bill_no", "nunique"),
            unique_customers=("customer_code", "nunique"),
        )
        .reset_index()
    )
    salesman_agg["margin_percent"] = salesman_agg.apply(
        lambda r: safe_div(r["gross_profit"], r["total_revenue"]) * 100, axis=1
    )
    salesman_agg["avg_transaction_value"] = salesman_agg.apply(
        lambda r: safe_div(r["total_revenue"], r["invoices"]), axis=1
    )
    salesman_agg = salesman_agg.sort_values("total_revenue", ascending=False)

    st.subheader("Salesman Ranking")
    cols = ["salesman_name", "total_revenue", "invoices", "unique_customers", "avg_transaction_value", "margin_percent"]
    st.dataframe(salesman_agg[cols])

    st.subheader("Top Salesmen by Revenue (with Margin %)")
    chart = alt.Chart(salesman_agg.head(15)).mark_bar().encode(
        x=alt.X("total_revenue:Q", title="Revenue"),
        y=alt.Y("salesman_name:N", sort="-x", title="Salesman"),
        color=alt.Color("margin_percent:Q", scale=alt.Scale(scheme="greens"), title="Margin %"),
        tooltip=["salesman_name", "total_revenue", "invoices", "margin_percent"],
    )
    st.altair_chart(chart)

    st.download_button(
        "Download salesman summary CSV",
        data=salesman_agg.to_csv(index=False),
        file_name="salesman_summary.csv",
    )


def growth_metrics(df):
    st.header("Growth & Trend Analysis")
    
    if check_empty_data(df, "Growth Metrics"):
        return

    if "transaction_date" not in df.columns:
        st.info("Insufficient data for growth analysis")
        return

    df_agg = df.copy()
    df_agg["year_month"] = df_agg["transaction_date"].dt.to_period("M")

    monthly = (
        df_agg.groupby("year_month")
        .agg(
            revenue=("total_revenue", "sum"),
            profit=("gross_profit", "sum"),
            qty=("quantity", "sum"),
        )
        .reset_index()
    )
    monthly["year_month"] = monthly["year_month"].astype(str)

    if len(monthly) >= 2:
        monthly["revenue_growth_pct"] = monthly["revenue"].pct_change() * 100
        st.subheader("Monthly Revenue Growth %")
        growth_chart = alt.Chart(monthly.dropna()).mark_bar().encode(
            x=alt.X("year_month:N", title="Month"),
            y=alt.Y("revenue_growth_pct:Q", title="Growth %"),
            color=alt.condition(
                alt.datum.revenue_growth_pct >= 0,
                alt.value("#2ecc71"),
                alt.value("#e74c3c"),
            ),
        )
        st.altair_chart(growth_chart)

    st.subheader("Monthly Revenue & Profit Trend")
    base = alt.Chart(monthly).encode(x=alt.X("year_month:N", title="Month"))
    
    revenue_line = base.mark_line(point=True, color="steelblue").encode(
        y=alt.Y("revenue:Q", title="Revenue", axis=alt.Axis(titleColor="steelblue", labelColor="steelblue"))
    )
    profit_line = base.mark_line(point=True, color="orange").encode(
        y=alt.Y("profit:Q", title="Profit", axis=alt.Axis(titleColor="orange", labelColor="orange"))
    )

    trend_chart = alt.layer(revenue_line, profit_line).resolve_scale(y="independent")
    st.altair_chart(trend_chart)

    st.dataframe(monthly)


def to_excel_bytes(sheets):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for name, sheet_df in sheets.items():
            sheet_df.to_excel(writer, sheet_name=name[:31], index=False)
    return buffer.getvalue()


def main():
    st.sidebar.title("Filters")
    df = load_data()
    if df.empty:
        st.warning("No data found in master_sales_analysis.csv")
        return

    df = filter_df(df)
    by_prod = build_product_summary(df)
    by_cust = build_customer_summary(df)

    tabs = st.tabs(
        [
            "Overview",
            "Product",
            "Customer",
            "Advanced Customer",
            "Salesman",
            "Growth",
            "Forecasting",
            "Market Basket",
            "Financial",
            "Logistics",
        ]
    )
    with tabs[0]:
        overview_tab(df)
    with tabs[1]:
        product_tab(df)
    with tabs[2]:
        customer_tab(df)
    with tabs[3]:
        advanced_customer_tab(df)
    with tabs[4]:
        salesman_tab(df)
    with tabs[5]:
        growth_metrics(df)
    with tabs[6]:
        forecast_tab(df)
    with tabs[7]:
        market_basket_tab(df)
    with tabs[8]:
        financial_tab(df)
    with tabs[9]:
        logistics_tab(df)

    st.download_button("Download filtered CSV", data=df.to_csv(index=False), file_name="master_filtered.csv")

    export_sheets = {
        "filtered": df,
        "product_summary": by_prod,
        "customer_summary": by_cust,
    }
    excel_bytes = to_excel_bytes(export_sheets)
    st.download_button(
        "Export all to Excel",
        data=excel_bytes,
        file_name="analytics_export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


if __name__ == "__main__":
    main()
