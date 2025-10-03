# 📊 E-Commerce Data Analysis with Streamlit
# Author: Ayesha Arshad
# -------------------------------------------


# ============ 1. IMPORT LIBRARIES ============
import pandas as pd
import plotly.express as px
import streamlit as st

# ============ 2. LOAD DATA ============
@st.cache_data
def load_data():
    df = pd.read_csv("ecommerce_dataset.csv")
    df = df.drop_duplicates()

    # Convert order_date column
    df['order_date'] = pd.to_datetime(df['order_date'])
    df['YearMonth'] = df['order_date'].dt.to_period("M")

    # Compute Sales column
    df['Sales'] = df['quantity'] * df['price'] * (1 - df['discount'])

    return df

df = load_data()

# ============ 3. INTRODUCTION ============
st.title("📊 E-Commerce Data Analysis Dashboard")
st.write("""
This dashboard explores customer behavior, sales trends, 
and product performance. It includes KPIs, charts, 
and insights useful for decision-making.
""")

# ============ 4. SIDEBAR FILTERS ============
st.sidebar.header("🔎 Filters")
categories = st.sidebar.multiselect("Select Categories", df['category'].unique())
if categories:
    df = df[df['category'].isin(categories)]

# ============ 5. KPIs ============
total_sales = df['Sales'].sum()
avg_order_value = df['Sales'].mean()
unique_customers = df['customer_id'].nunique()

col1, col2, col3 = st.columns(3)
col1.metric("Total Sales", f"${total_sales:,.0f}")
col2.metric("Avg. Order Value", f"${avg_order_value:,.2f}")
col3.metric("Unique Customers", unique_customers)

# ============ 6. SALES BY CATEGORY ============
st.subheader("🛒 Sales by Category")
category_sales = df.groupby("category")["Sales"].sum().reset_index()
fig = px.bar(category_sales, x="category", y="Sales",
             title="Sales by Category",
             text_auto=True, color="category",
             color_discrete_sequence=px.colors.sequential.Tealgrn)
st.plotly_chart(fig, use_container_width=True)

# ============ 7. MONTHLY SALES TREND ============
st.subheader("📈 Monthly Sales Trend")
monthly_sales = df.groupby(df['order_date'].dt.to_period("M"))["Sales"].sum().reset_index()
monthly_sales['order_date'] = monthly_sales['order_date'].astype(str)
fig2 = px.line(monthly_sales, x="order_date", y="Sales",
               title="Monthly Sales Trend",
               markers=True,
               color_discrete_sequence=["#636EFA"])
st.plotly_chart(fig2, use_container_width=True)

# ============ 8. TOP CUSTOMERS ============
st.subheader("👤 Top 10 Customers")
top_customers = df.groupby("customer_id")["Sales"].sum().nlargest(10).reset_index()
fig3 = px.bar(top_customers, x="customer_id", y="Sales",
              title="Top 10 Customers",
              text_auto=True, color="Sales",
              color_continuous_scale="Viridis")
st.plotly_chart(fig3, use_container_width=True)

# ============ 9. TOP PRODUCTS ============
st.subheader("📦 Top 10 Products")
top_products = df.groupby("product_id")["Sales"].sum().nlargest(10).reset_index()
fig4 = px.bar(top_products, x="product_id", y="Sales",
              title="Top 10 Products",
              text_auto=True, color="Sales",
              color_continuous_scale="Blues")
st.plotly_chart(fig4, use_container_width=True)

# ============ 10. CONCLUSION ============
st.subheader("✅ Conclusion")
st.markdown("""
- **Electronics** or other top categories dominate sales.
- Strong **seasonality** with spikes in Nov–Dec.
- **Top customers & products** drive major revenue.  
👉 These insights can help improve targeted marketing and inventory planning.
""")
