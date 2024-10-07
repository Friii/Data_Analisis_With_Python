import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency
sns.set(style= 'dark')


# Function daily order
def create_daily_order_df(df):
    daily_order_df = df.resample(rule="D", on= 'order_purchase_timestamp').agg({
        "order_id" : "nunique",
        "price" : "sum",
    })
    daily_order_df = daily_order_df.reset_index()
    daily_order_df.rename(columns={
        'order_id' : "order_count",
        'price' : "revenue"}, inplace=True)
    
    return daily_order_df

# Function product order 
def create_product_summaries_df(df):
    sum_order_items_df = all_df.groupby("product_category_name_english_x").agg({
        "product_id": "count",
    }).reset_index()
    sum_order_items_df.columns = ["product_category_english", "product_sold"]
    sum_order_items_df.product_category_english = sum_order_items_df.product_category_english.apply(lambda x: " ".join(x.split("_")).title())
    return sum_order_items_df


# Function Customers Best City
def visual_data(s, S, title):
    customer_df = all_df.groupby(f"customer_{s}").agg({
        "customer_id": "nunique",
    }).reset_index()
    customer_df.columns = [S, "Customers"]
    customer_df.sort_values(by="Customers", ascending=False, inplace=True)

    best_city_df = customer_df[:3].copy()

    others_df = pd.DataFrame({
        S: ['Others'],
        'Customers': [customer_df[3:]["Customers"].sum()]
    })
    finishing_df = pd.concat([best_city_df, others_df], ignore_index=True)
    fig, ax = plt.subplots(figsize=(6, 6))
    plt.pie(
        x=finishing_df["Customers"],
        labels=finishing_df[S],
        autopct='%1.1f%%',
        wedgeprops = {'width': .75}
    )
    ax.set_title(title)
    st.pyplot(fig)

def create_rfm_df(df):
    rfm_df = all_df.groupby(by="customer_id").agg({
        "order_purchase_timestamp": "max",
        "order_id": "count",
        "price": "sum",
        "freight_value": "sum",
    }).reset_index()

    rfm_df["revenue"] = rfm_df["price"] + rfm_df["freight_value"]
    rfm_df.drop(["price", "freight_value"], axis=1, inplace=True)
    rfm_df.columns = ["customer_id", "max_order_timestamp", "frequency", "monetary"]
    
    rfm_df["max_order_timestamp"] = rfm_df["max_order_timestamp"].dt.date
    recent_date = all_df["order_purchase_timestamp"].dt.date.max()
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days)

    rfm_df.drop("max_order_timestamp", axis=1, inplace=True)
    
    return rfm_df

# Read CSV file
all_df = pd.read_csv("dashboard/all_data.csv")
all_df.reset_index(inplace=True)

datetime_columns = ["order_purchase_timestamp","order_approved_at","order_delivered_carrier_date","order_delivered_customer_date","order_estimated_delivery_date"]
for column in datetime_columns:
  all_df[column] = pd.to_datetime(all_df[column])
minimum_date = all_df["order_purchase_timestamp"].min()
maximum_date = all_df["order_purchase_timestamp"].max()

with st.sidebar:
    st.title("Dashboard Zeta Mart")
    st.image("dashboard/download.png")

    st.header("Pilih Periode")
    start_date = st.date_input(
        label='Awal',min_value=minimum_date,
        max_value=maximum_date,
        value=minimum_date,
    )
    end_date = st.date_input(
        label='Akhir',min_value=minimum_date,
        max_value=maximum_date,
        value=maximum_date,
    )
    if start_date > end_date:
        [start_date, end_date] = [end_date, start_date]


# Visualisasi Daily Order
main_df = all_df[(all_df["order_purchase_timestamp"] >= str(start_date)) & 
                (all_df["order_purchase_timestamp"] <= str(end_date))]
order_df = create_daily_order_df(main_df)

with st.container():
    st.subheader('Order Harian Zeta Mart🛒')
    
    col1, col2 = st.columns(2)
    
    with col1:
        total_orders = order_df.order_count.sum()
        st.metric("Total Order", value=total_orders)

    with col2:
        total_revenue = format_currency(order_df.revenue.sum(), "AUD", locale='es_CO') 
        st.metric("Total Revenue", value=total_revenue)

    fig, ax = plt.subplots(figsize=(20, 10))
    ax.plot(
        order_df["order_purchase_timestamp"],
        order_df["order_count"],
        marker='o', 
        linewidth=2,
        color="#A0BAFF"
    )
    ax.tick_params(axis='y', labelsize=20)
    ax.tick_params(axis='x', labelsize=18)

    st.pyplot(fig)

# Visualisasi Product Sold 
product_df = create_product_summaries_df(main_df)

with st.container():
    st.subheader("Data Produk Penjualan")
    fig, ax = plt.subplots(nrows=2, ncols=1, figsize=(32, 36))
    colors = ["#90CAF9", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

    sns.barplot(x="product_sold", y="product_category_english", hue="product_category_english", data=product_df.sort_values(by="product_sold", ascending=False).head(5), palette=colors, ax=ax[0])
    ax[0].set_ylabel("Produk")
    ax[0].set_xlabel("Angka penjualan", fontsize=35)
    ax[0].set_title("Produk dengan Penjualan Terbanyak", loc="center", fontsize=50)
    ax[0].tick_params(axis='y', labelsize=75)
    ax[0].tick_params(axis='x', labelsize=35)

    sns.barplot(x="product_sold", y="product_category_english", hue="product_category_english", data=product_df.sort_values(by="product_sold", ascending=True).head(5), palette=colors, ax=ax[1])
    ax[1].set_ylabel("Produk dengan penjualan paling sedikit")
    ax[1].set_xlabel("Angka penjualan", fontsize=35)
    ax[1].invert_xaxis()
    ax[1].yaxis.set_label_position("right")
    ax[1].yaxis.tick_right()
    ax[1].set_title("Produk dengan Penjualan Paling Sedikit", loc="center", fontsize=50)
    ax[1].tick_params(axis='y', labelsize=35)
    ax[1].tick_params(axis='x', labelsize=35)
    
    st.pyplot(fig)

# Visualisasi Recency, Frequency and 
with st.container():
    st.subheader("Demografi Customer")

    col1, col2 = st.columns(2)

    with col1:
        visual_data("state", "State", "Perhitungan Customer dari Negara Bagian (State)") 

    with col2:
        visual_data("city", "City", "Perhitungan Customer dari Kota (City)") 

rfm_df = create_rfm_df(main_df)
with st.container():
    st.subheader("Pelanggan Terbaik Berdasarkan Parameter RFM")

    col1, col2, col3 = st.columns(3)
    
    with col1:
        avg_recency = round(rfm_df.recency.mean(), 1)
        st.metric("Average Recency (days)", value=avg_recency)
    
    with col2:
        avg_frequency = round(rfm_df.frequency.mean(), 2)
        st.metric("Average Frequency", value=avg_frequency)
    
    with col3:
        avg_frequency = format_currency(rfm_df.monetary.mean(), "AUD", locale='es_CO') 
        st.metric("Average Monetary", value=avg_frequency)

    fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(25, 10))
    colors = ["#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9"]
    
    sns.barplot(y="recency", hue="customer_id", data=rfm_df.sort_values(by="recency", ascending=True).head(10), palette=colors, ax=ax[0])
    ax[0].set_ylabel(None)
    ax[0].set_xlabel("customer_id", fontsize=32)
    ax[0].set_title("By Recency (days)", loc="center", fontsize=42)
    ax[0].tick_params(axis='y', labelsize=32)
    ax[0].tick_params(axis='x', labelsize=35)

    sns.barplot(y="frequency", hue="customer_id", data=rfm_df.sort_values(by="frequency", ascending=False).head(5), palette=colors, ax=ax[1])
    ax[1].set_ylabel(None)
    ax[1].set_xlabel("customer_id", fontsize=32)
    ax[1].set_title("By Frequency", loc="center", fontsize=42)
    ax[1].tick_params(axis='y', labelsize=32)
    ax[1].tick_params(axis='x', labelsize=35)

    sns.barplot(y="monetary", hue="customer_id", data=rfm_df.sort_values(by="monetary", ascending=False).head(5), palette=colors, ax=ax[2])
    ax[2].set_ylabel(None)
    ax[2].set_xlabel("customer_id", fontsize=32)
    ax[2].set_title("By Monetary", loc="center", fontsize=42)
    ax[2].tick_params(axis='y', labelsize=32)
    ax[2].tick_params(axis='x', labelsize=35)
    
    st.pyplot(fig)