# 📊 E-Commerce Data Analysis with Streamlit
# Author: Ayesha Arshad
# -------------------------------------------
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="E-Commerce EDA")

# ---------- Helpers ----------
@st.cache_data
def load_df(path="ecommerce_dataset.csv"):
    """Load CSV and normalize column names to lowercase, return df."""
    df = pd.read_csv(path)
    # normalize columns to lowercase and strip spaces
    df.columns = [c.strip().lower() for c in df.columns]
    return df

def safe_to_datetime(df, candidates, new_col="order_date"):
    """Find a date column from candidates and create standard order_date col."""
    for c in candidates:
        if c in df.columns:
            try:
                df[new_col] = pd.to_datetime(df[c], errors="coerce")
                return df
            except Exception:
                continue
    # no date col found: create NaT column
    df[new_col] = pd.NaT
    return df

def compute_sales(df):
    """Create Sales column if not present. Prefer existing 'sales', else compute."""
    if "sales" in df.columns:
        # ensure numeric
        df["sales"] = pd.to_numeric(df["sales"], errors="coerce").fillna(0)
        return df
    # expected components: quantity, price, discount (discount as fraction or percent)
    q = None
    p = None
    d = None
    if "quantity" in df.columns:
        q = pd.to_numeric(df["quantity"], errors="coerce").fillna(0)
    if "price" in df.columns:
        p = pd.to_numeric(df["price"], errors="coerce").fillna(0)
    if "discount" in df.columns:
        d = pd.to_numeric(df["discount"], errors="coerce").fillna(0)
    # If discount looks like percent (0-100), convert to fraction when >1
    if d is not None:
        if d.max() > 1:
            d = d / 100.0
    # Build Sales
    if q is not None and p is not None:
        if d is not None:
            df["sales"] = q * p * (1 - d)
        else:
            df["sales"] = q * p
    else:
        # Fallback: try order_total or amount fields
        for fallback in ["order_total", "amount", "total"]:
            if fallback in df.columns:
                df["sales"] = pd.to_numeric(df[fallback], errors="coerce").fillna(0)
                break
        else:
            # As last resort zero sales
            df["sales"] = 0.0
    return df

def safe_groupby_sum(df, by, col="sales"):
    if by not in df.columns:
        return pd.DataFrame(columns=[by, col])
    g = df.groupby(by)[col].sum().reset_index()
    return g

# ---------- Load & prepare data ----------
st.sidebar.header("Data & Filters")

try:
    df = load_df("ecommerce_dataset.csv")
except FileNotFoundError:
    st.error("Could not find 'ecommerce_dataset.csv' in the app folder. Upload it or place it next to this script.")
    st.stop()
except Exception as e:
    st.error(f"Failed to load CSV: {e}")
    st.stop()

# show user the detected columns
st.sidebar.markdown("**Detected columns:**")
st.sidebar.write(list(df.columns))

# ensure order_date column exists (detect common names)
date_candidates = ["order_date", "order date", "date", "orderdate"]
df = safe_to_datetime(df, date_candidates, new_col="order_date")

# compute Sales
df = compute_sales(df)

# add YearMonth for monthly grouping (string for plotting)
df["yearmonth"] = df["order_date"].dt.to_period("M").astype(str)

# Sidebar filters (only show filters for columns present)
with st.sidebar.form("filters"):
    # Date range filter if order_date exists
    if df["order_date"].notna().any():
        min_date = df["order_date"].min()
        max_date = df["order_date"].max()
        date_range = st.date_input("Order date range", value=(min_date, max_date))
    else:
        date_range = None

    # Category filter
    if "category" in df.columns:
        cats = st.multiselect("Category", options=sorted(df["category"].dropna().unique()))
    else:
        cats = []

    # Region filter
    if "region" in df.columns:
        regions = st.multiselect("Region", options=sorted(df["region"].dropna().unique()))
    else:
        regions = []

    # Payment method filter
    if "payment_method" in df.columns:
        payments = st.multiselect("Payment method", options=sorted(df["payment_method"].dropna().unique()))
    else:
        payments = []

    submit = st.form_submit_button("Apply filters")

# Apply filters to working df copy
df_work = df.copy()
if date_range and isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    start, end = date_range
    # convert to datetime
    start = pd.to_datetime(start)
    end = pd.to_datetime(end)
    df_work = df_work[(df_work["order_date"] >= start) & (df_work["order_date"] <= end)]

if cats:
    df_work = df_work[df_work["category"].isin(cats)]
if regions:
    df_work = df_work[df_work["region"].isin(regions)]
if payments:
    df_work = df_work[df_work["payment_method"].isin(payments)]

# ---------- Top-level KPIs ----------
st.title("📊 E-Commerce Data Analysis Dashboard (Converted from EDA.html)")
st.markdown("A robust Streamlit version that recreates the charts & analyses from your uploaded EDA.")

total_sales = df_work["sales"].sum()
avg_order_value = df_work["sales"].mean() if len(df_work) > 0 else 0
unique_customers = df_work["customer_id"].nunique() if "customer_id" in df_work.columns else 0

k1, k2, k3 = st.columns([1.5,1.5,1])
k1.metric("Total Sales", f"${total_sales:,.2f}")
k2.metric("Avg Order Value", f"${avg_order_value:,.2f}")
k3.metric("Unique Customers", f"{unique_customers}")

st.markdown("---")

# ---------- Sales by Category (bar) ----------
if "category" in df_work.columns:
    st.subheader("🛒 Sales by Category")
    category_sales = safe_groupby_sum(df_work, "category", "sales").sort_values("sales", ascending=False)
    if not category_sales.empty:
        fig_cat = px.bar(category_sales, x="category", y="sales",
                         title="Sales by Category",
                         text_auto=True, color="category",
                         color_discrete_sequence=px.colors.sequential.Tealgrn)
        fig_cat.update_layout(showlegend=False, yaxis_title="Sales")
        st.plotly_chart(fig_cat, use_container_width=True)
    else:
        st.info("No category sales to display for current filters.")
else:
    st.info("Column 'category' not found in dataset; skipping Sales by Category chart.")

# ---------- Sales by Payment Method (bar) ----------
if "payment_method" in df_work.columns:
    st.subheader("💳 Sales by Payment Method")
    pm_sales = safe_groupby_sum(df_work, "payment_method", "sales").sort_values("sales", ascending=False)
    if not pm_sales.empty:
        fig_pm = px.bar(pm_sales, x="payment_method", y="sales", text_auto=True,
                        title="Sales by Payment Method")
        fig_pm.update_layout(xaxis_title="Payment Method", yaxis_title="Sales", showlegend=False)
        st.plotly_chart(fig_pm, use_container_width=True)
    else:
        st.info("No payment method sales to display for current filters.")
else:
    st.info("Column 'payment_method' not found; skipping Payment Method chart.")

# ---------- Monthly Sales Trend (line) ----------
if df_work["order_date"].notna().any():
    st.subheader("📈 Monthly Sales Trend")
    monthly_sales = df_work.groupby(df_work["order_date"].dt.to_period("M"))["sales"].sum().reset_index()
    monthly_sales["order_date"] = monthly_sales["order_date"].astype(str)
    monthly_sales = monthly_sales.sort_values("order_date")
    if not monthly_sales.empty:
        fig_month = px.line(monthly_sales, x="order_date", y="sales",
                            title="Monthly Sales Trend", markers=True)
        fig_month.update_layout(xaxis_title="Year-Month", yaxis_title="Sales")
        st.plotly_chart(fig_month, use_container_width=True)
    else:
        st.info("No monthly sales to display with current filters.")
else:
    st.info("No valid order_date values found; skipping Monthly Sales Trend.")

# ---------- Top 10 Customers ----------
if "customer_id" in df_work.columns:
    st.subheader("👥 Top 10 Customers by Sales")
    top_customers = df_work.groupby("customer_id")["sales"].sum().nlargest(10).reset_index()
    if not top_customers.empty:
        fig_cust = px.bar(top_customers, x="customer_id", y="sales", title="Top 10 Customers",
                          text_auto=True, color="sales", color_continuous_scale="Viridis")
        fig_cust.update_layout(xaxis_title="Customer ID", yaxis_title="Sales", showlegend=False)
        st.plotly_chart(fig_cust, use_container_width=True)
    else:
        st.info("No customer sales to show.")
else:
    st.info("Column 'customer_id' not found; skipping Top Customers chart.")

# ---------- Top 10 Products ----------
# If product name not available, use product_id
prod_col = "product_id" if "product_id" in df_work.columns else ("productname" if "productname" in df_work.columns else None)
if prod_col:
    st.subheader("📦 Top 10 Products by Sales")
    top_products = df_work.groupby(prod_col)["sales"].sum().nlargest(10).reset_index()
    if not top_products.empty:
        fig_prod = px.bar(top_products, x=prod_col, y="sales",
                          title="Top 10 Products by Sales", text_auto=True,
                          color="sales", color_continuous_scale="Blues")
        fig_prod.update_layout(xaxis_title=prod_col, yaxis_title="Sales", showlegend=False)
        st.plotly_chart(fig_prod, use_container_width=True)
    else:
        st.info("No product sales to display.")
else:
    st.info("No product identifier column found; skipping Top Products chart.")

# ---------- Category vs Region Heatmap (if present) ----------
if ("category" in df_work.columns) and ("region" in df_work.columns):
    st.subheader("🗺️ Sales by Category and Region (Heatmap)")
    pivot = df_work.pivot_table(values="sales", index="category", columns="region", aggfunc="sum", fill_value=0)
    if not pivot.empty:
        fig_heat = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=list(pivot.columns),
            y=list(pivot.index),
            hovertemplate="Region=%{x}<br>Category=%{y}<br>Sales=%{z}<extra></extra>"
        ))
        fig_heat.update_layout(title="Category vs Region Sales Heatmap", xaxis_title="Region", yaxis_title="Category")
        st.plotly_chart(fig_heat, use_container_width=True)
    else:
        st.info("Heatmap has no data for current filters.")
else:
    st.info("Need both 'category' and 'region' to compute Category vs Region heatmap.")

# ---------- Discount analysis ----------
if "discount" in df_work.columns:
    st.subheader("🏷️ Discount vs Sales")
    # ensure discount as fraction
    disc = pd.to_numeric(df_work["discount"], errors="coerce").fillna(0)
    if disc.max() > 1:
        disc = disc / 100
    df_work["_discount_frac"] = disc
    # aggregate by rounded discount bins
    df_work["_disc_bin"] = (df_work["_discount_frac"] * 100).round().astype(int)
    disc_agg = df_work.groupby("_disc_bin")["sales"].sum().reset_index().sort_values("_disc_bin")
    if not disc_agg.empty:
        fig_disc = px.bar(disc_agg, x="_disc_bin", y="sales", title="Sales by Discount (%) bin",
                          labels={"_disc_bin":"Discount (%)", "sales":"Sales"}, text_auto=True)
        st.plotly_chart(fig_disc, use_container_width=True)
    else:
        st.info("No discount analysis data available.")
else:
    st.info("Column 'discount' not found; skipping discount analysis.")

# ---------- Quantity distribution ----------
if "quantity" in df_work.columns:
    st.subheader("🔢 Quantity distribution (orders)")
    qty = pd.to_numeric(df_work["quantity"], errors="coerce").fillna(0)
    if len(qty) > 0:
        fig_qty = px.histogram(df_work, x="quantity", nbins=30, title="Order quantity distribution")
        st.plotly_chart(fig_qty, use_container_width=True)
    else:
        st.info("No quantity data to plot.")
else:
    st.info("Column 'quantity' not found; skipping quantity distribution.")

# ---------- Raw data preview ----------
with st.expander("Show data (first 200 rows)"):
    st.write(df_work.head(200))

