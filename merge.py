import pandas as pd


def generate_master_sales_csv():
    # 1. Load semua file CSV yang diperlukan
    df_transaction = pd.read_csv('Transaction.csv')
    df_product = pd.read_csv('Product.csv')
    df_category = pd.read_csv('Category.csv')
    df_customers = pd.read_csv('customers.csv')
    df_delivery = pd.read_csv('Delivery.csv')

    # 2. Standardize/rename transaction columns to avoid ambiguity
    df_transaction = df_transaction.rename(columns={
        'id': 'transaction_id',
        'billNo': 'bill_no',
        'date': 'transaction_date',
        'qty': 'quantity',
        'price': 'selling_price',
        'total': 'total_revenue',
        'paymentType': 'payment_type',
        'status': 'payment_status',
        'sales': 'salesman_name',
        'customerId': 'customer_id',
        'productId': 'product_id'
    })

    # 3. Rename product/category/customer/delivery columns for clarity
    df_product = df_product.rename(columns={
        'id': 'product_pk',
        'productCode': 'product_code',
        'name': 'product_name',
        'size': 'product_size',
        'basePrice': 'base_price',
        'categoryId': 'category_id'
    })

    df_category = df_category.rename(columns={'id': 'category_pk', 'name': 'category_name'})

    df_customers = df_customers.rename(columns={
        'id': 'customer_pk',
        'customerCode': 'customer_code',
        'nama': 'customer_name',
        'provinsi': 'provinsi',
        'kota': 'kota',
        'tipeChannel': 'customer_channel'
    })

    df_delivery = df_delivery.rename(columns={
        'transactionId': 'transaction_id',
        'deliveryDate': 'delivery_date',
        'status': 'delivery_status',
        'nopol': 'delivery_vehicle'
    })

    # 4. Merge step-by-step using explicit keys
    master_df = pd.merge(
        df_transaction,
        df_product[['product_pk', 'product_code', 'product_name', 'product_size', 'base_price', 'category_id']],
        left_on='product_id',
        right_on='product_pk',
        how='left'
    )

    master_df = pd.merge(
        master_df,
        df_category[['category_pk', 'category_name']],
        left_on='category_id',
        right_on='category_pk',
        how='left'
    )

    master_df = pd.merge(
        master_df,
        df_customers[['customer_pk', 'customer_code', 'customer_name', 'provinsi', 'kota', 'customer_channel']],
        left_on='customer_id',
        right_on='customer_pk',
        how='left'
    )

    master_df = pd.merge(
        master_df,
        df_delivery[['transaction_id', 'delivery_date', 'delivery_status', 'delivery_vehicle']],
        on='transaction_id',
        how='left'
    )

    # 5. Derived / cleaned columns
    # Ensure numeric types
    master_df['quantity'] = pd.to_numeric(master_df['quantity'], errors='coerce').fillna(0)
    master_df['total_revenue'] = pd.to_numeric(master_df['total_revenue'], errors='coerce').fillna(0)
    master_df['base_price'] = pd.to_numeric(master_df['base_price'], errors='coerce').fillna(0)

    # Gross profit and margin percent (handle zero revenue)
    master_df['gross_profit'] = master_df['total_revenue'] - (master_df['base_price'] * master_df['quantity'])
    master_df['margin_percent'] = master_df.apply(lambda r: (r['gross_profit'] / r['total_revenue'] * 100)
                                                   if r['total_revenue'] and r['total_revenue'] != 0 else 0,
                                                   axis=1)

    # Customer city/prov combined
    master_df['customer_city_prov'] = master_df['kota'].fillna('') + ', ' + master_df['provinsi'].fillna('')

    # Parse datetimes and delivery lead time
    master_df['transaction_date'] = pd.to_datetime(master_df['transaction_date'], errors='coerce')
    master_df['delivery_date'] = pd.to_datetime(master_df['delivery_date'], errors='coerce')
    master_df['delivery_lead_time_days'] = (master_df['delivery_date'] - master_df['transaction_date']).dt.days

    # Flags
    master_df['is_credit'] = master_df['payment_type'].astype(str).str.upper() == 'CREDIT'
    master_df['is_paid'] = master_df['payment_status'].astype(str).str.upper() == 'PAID'
    master_df['is_delivered'] = master_df['delivery_status'].astype(str).str.upper() == 'DELIVERED'

    # Surrogate salesman id: hash of salesman_name if no explicit id available
    master_df['salesman_id'] = master_df['salesman_name'].fillna('').apply(lambda s: pd.util.hash_pandas_object(pd.Series([s])).iloc[0])

    # 6. Select and order final columns for analytics contract
    final_cols = [
        'transaction_id', 'bill_no', 'transaction_date', 'delivery_date', 'delivery_lead_time_days',
        'customer_id', 'customer_pk', 'customer_code', 'customer_name', 'customer_channel', 'customer_city_prov',
        'product_id', 'product_pk', 'product_code', 'product_name', 'product_size', 'category_id', 'category_name',
        'quantity', 'selling_price', 'total_revenue', 'base_price', 'gross_profit', 'margin_percent',
        'payment_type', 'payment_status', 'is_credit', 'is_paid',
        'delivery_status', 'delivery_vehicle', 'is_delivered',
        'salesman_name', 'salesman_id'
    ]

    # Keep only columns that exist in master_df (defensive)
    final_cols = [c for c in final_cols if c in master_df.columns]
    final_df = master_df[final_cols]

    # 7. Export ke CSV
    final_df.to_csv('master_sales_analysis.csv', index=False)
    print("File 'master_sales_analysis.csv' berhasil dibuat!")


if __name__ == '__main__':
    generate_master_sales_csv()