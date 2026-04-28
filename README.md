# Sales Analytics MVP - Complete Implementation

A comprehensive Streamlit application for sales analytics with advanced features including RFM analysis, forecasting, market basket analysis, and financial metrics.

## ✅ Project Status: Complete

**Phase 0 (Data Preparation):** ✅ Complete
- ETL pipeline (merge.py) with normalized data schema
- Master CSV generation with 30+ derived fields
- Data quality validation with automated checks

**Phase 1 (MVP):** ✅ Complete  
- Interactive Streamlit dashboard with 10 tabs
- Sidebar filters (Date, Category, Product, Channel, Area, Salesman)
- KPI metrics and trend analysis
- CSV/Excel export functionality

**Phase 2+ (Advanced Analytics):** ✅ Complete
- RFM scoring with customer segmentation
- Churn/retention analysis with adjustable windows
- Customer Lifetime Value (CLV) calculations
- Forecasting with moving average
- Market basket analysis with association rules
- Financial analytics (aging, DSO, collections)
- Growth metrics (YoY/MoM analysis)
- Salesman performance dashboard
- Logistics analytics with lead-time tracking

**TIER 1 Enhancements:** ✅ Complete
- RFM scoring legend with explanation guide
- Interactive churn detection parameters (slider controls)
- Negative margin product warnings with details
- Payment method distribution visualization
- Salesman performance dashboard with rankings
- Growth & trend analysis tab with YoY/MoM metrics
- Deprecated API migration (use_container_width → width)
- Fixed Altair visualization compatibility

**Data Quality Improvements:** ✅ Complete
- Fixed 429 zero base_price entries
- Identified 8 promotional pricing transactions
- Added data quality warnings with expandable detail view

**Error Handling & Robustness:** ✅ Complete
- Empty data validation across all tabs
- User-friendly warning messages
- Edge case handling
- Input validation for filters and parameters

## Features Overview

### Dashboard Tabs (10 Total)

1. **Overview Dashboard**
   - KPI metrics (Revenue, Quantity, AOV, Gross Profit)
   - Weekly revenue trend chart
   - Top categories by revenue
   - Margin distribution histogram
   - Payment method split (pie chart)
   - Data quality summary with flagged issues

2. **Product Analysis**
   - Top 20 products by revenue with category coloring
   - Margin vs Revenue scatter plot (interactive)
   - Negative margin product alerts
   - Top 50 products detailed table
   - CSV export

3. **Customer Analysis**
   - Top 20 customers by revenue with channel breakdown
   - Customer revenue distribution histogram
   - Top 50 customers detailed table
   - CSV export

4. **Advanced Customer Analytics**
   - RFM scoring (Recency, Frequency, Monetary) with guide
   - Customer segmentation by RFM total
   - Churn/retention detection (adjustable 7-60 day windows)
   - Customer Lifetime Value (CLV) projections
   - Retention rate and churn metrics

5. **Salesman Performance Dashboard**
   - Salesman ranking by revenue
   - Avg transaction value per salesman
   - Unique customer count per salesman
   - Margin % per salesman (color-coded bar chart)
   - CSV export

6. **Growth & Trend Analysis**
   - Monthly revenue growth percentage (green/red coloring)
   - YoY/MoM trend analysis
   - Dual-axis chart (Revenue + Profit by month)
   - Detailed monthly metrics table

7. **Forecasting**
   - Mode selection (by Product or Channel)
   - Adjustable moving average window (2-12 weeks)
   - Variable forecast horizon (2-12 weeks)
   - Actual vs forecast line chart
   - Detailed forecast table

8. **Market Basket Analysis**
   - Association rule mining (Antecedent → Consequent)
   - Support, Confidence, Lift metrics
   - Adjustable minimum thresholds (sliders)
   - Top 100 rules by lift/confidence
   - CSV export of rules

9. **Financial Analytics**
   - Outstanding receivable tracking
   - Days Sales Outstanding (DSO) calculation
   - Collection efficiency percentage
   - Aging buckets (0-30, 31-60, 61-90, 90+ days)
   - Aging bucket bar chart
   - Detailed outstanding receivable invoice list

10. **Logistics Analytics**
    - Delivery lead-time distribution
    - Average and median lead time metrics
    - On-time delivery percentage (≤3 days)
    - Top 10 delivery vehicles

## Installation & Running

```bash
# Install dependencies
pip install -r requirements.txt

# Generate master analytics CSV (one-time)
python merge.py

# Run Streamlit app
streamlit run app.py
```

App opens at: `http://localhost:8501`

## Data Quality Report

| Metric | Value |
|--------|-------|
| Total Transactions | 523 |
| Missing Base Price | 0 ✅ |
| Zero Base Price | 0 ✅ |
| Negative Gross Profit | 8 (promotional pricing) |
| Zero Quantity | 0 ✅ |
| Duplicate Transaction IDs | 0 ✅ |

## Testing & Validation

```bash
# Run unit tests (2/2 passing)
python -m unittest discover -s tests -p "test_*.py" -v

# Validate syntax
python -m py_compile app.py

# Check data quality
python data_quality.py
```

## Version History

- **v1.0 (2026-04-28):** Complete MVP + Advanced Analytics + TIER 1 + Error Handling
  - All phases (0, 1, 2+) complete
  - Comprehensive error handling
  - Data quality fixes
  - Full documentation
