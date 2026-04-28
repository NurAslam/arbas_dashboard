import pandas as pd


def run_checks(path='master_sales_analysis.csv'):
    df = pd.read_csv(path, parse_dates=['transaction_date', 'delivery_date'], low_memory=False)
    report = {}

    report['rows'] = len(df)
    report['missing_base_price'] = int(df['base_price'].isna().sum()) if 'base_price' in df.columns else 0
    report['zero_base_price'] = int((df.get('base_price', pd.Series()).fillna(0) == 0).sum())
    report['negative_gross_profit'] = int((df.get('gross_profit', pd.Series()) < 0).sum())
    report['zero_quantity'] = int((df.get('quantity', pd.Series()) == 0).sum())
    report['duplicate_transaction_ids'] = int(df['transaction_id'].duplicated().sum()) if 'transaction_id' in df.columns else 0

    # Top offenders samples
    issues = {}
    if 'base_price' in df.columns:
        issues['base_price_zero_sample'] = df[df['base_price'].fillna(0) == 0].head(10).to_dict(orient='records')
    if 'gross_profit' in df.columns:
        neg_profit = df[df['gross_profit'] < 0][['transaction_id', 'bill_no', 'product_code', 'product_name', 
                                                    'quantity', 'selling_price', 'base_price', 'gross_profit', 'margin_percent']].head(10)
        issues['negative_gross_profit_sample'] = neg_profit.to_dict(orient='records')

    return report, issues


if __name__ == '__main__':
    rpt, issues = run_checks()
    print('Data quality summary:')
    for k, v in rpt.items():
        print(f"- {k}: {v}")
    print('\nSample issues:')
    for k, v in issues.items():
        print(f"\n{k} (showing up to 10 rows):")
        for r in v:
            print(r)
