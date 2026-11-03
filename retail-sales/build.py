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
    def page(name,keys):
        s='<!doctype html><meta charset="utf-8"><title>'+name+'</title><style>body{font:16px system-ui;max-width:960px;margin:48px auto;padding:0 24px;color:#173442;background:#f4f8fa}section{background:white;padding:24px;margin:20px 0;border-radius:12px;overflow:auto}td,th{padding:8px 14px;text-align:left}table{border-collapse:collapse}tr:nth-child(even){background:#eff7f7}meter{width:180px}</style><h1>'+name+'</h1><p>UK online retailer · Dec 2010–Nov 2011 · GBP</p>'
        for key in keys:
            d=tables[key].copy()
            s+='<section><h2>'+key[3:].replace('_',' ').title()+'</h2>'+d.round(2).to_html(index=False)
            if len(d)>1:
                col=d.select_dtypes('number').columns[0]
                for label,v in zip(d.iloc[:,0],d[col]):
                    from html import escape
                    s+=f'<div><meter max="{max(d[col].max(),1)}" value="{max(v,0)}"></meter> {escape(str(label))} · {v:,.2f}</div>'
            s+='</section>'
        Path(name.replace(' ','_')+'.html').write_text(s)
    page('Sales Dashboard',['01_scorecard','02_monthly_sales','03_markets'])
    page('Customers and Credits Dashboard',['04_customer_repeat','05_credit_hotspots','06_order_value'])
    t=tables['01_scorecard'].iloc[0]
    assert abs(t.sales_gbp-t.credit_gbp-t.net_gbp)<.01
    assert abs(tables['02_monthly_sales'].sales_gbp.sum()-t.sales_gbp)<.01
    print(len(raw),len(valid))
    for key,d in tables.items(): print(key,d.head(3).to_string(index=False))
if __name__=='__main__':
    build(sys.argv[1])
