from pathlib import Path
import sqlite3, sys
import pandas as pd

def build(source):
    raw = pd.read_excel(source, dtype={'InvoiceNo':str,'StockCode':str})
    valid = raw[raw.UnitPrice.gt(0) & raw.Quantity.ne(0)].copy()
    valid['Kind'] = 'Sale'
    valid.loc[valid.InvoiceNo.str.upper().str.startswith('C') | valid.Quantity.lt(0),'Kind'] = 'Credit'
    valid['AmountGBP'] = (valid.Quantity.abs()*valid.UnitPrice).round(2)
    valid['Month'] = valid.InvoiceDate.dt.strftime('%Y-%m')
    valid = valid[valid.Month.between('2010-12','2011-11')]
    valid['CustomerID'] = valid.CustomerID.astype('Int64')
    valid[['InvoiceNo','StockCode','Description','Country','CustomerID','Month','Kind','AmountGBP']].to_csv('Transactions.csv',index=False)
    with sqlite3.connect(':memory:') as db:
        valid.to_sql('Transactions',db,index=False)
        tables={}
        for p in sorted(Path('sql').glob('*.sql')):
            tables[p.stem]=pd.read_sql_query(p.read_text(),db)
    t=tables['01_scorecard'].iloc[0]
    assert abs(t.sales_gbp-t.credit_gbp-t.net_gbp)<.01
    assert abs(tables['02_monthly_sales'].sales_gbp.sum()-t.sales_gbp)<.01
    print(len(raw),len(valid))
    for key,d in tables.items(): print(key,d.head(3).to_string(index=False))
if __name__=='__main__':
    build(sys.argv[1])
