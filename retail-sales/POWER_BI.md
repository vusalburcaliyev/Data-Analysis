# Build the two pages in Power BI

Run the Python build, then use **Get data → Text/CSV** to import Transactions.csv as Transactions.
Set InvoiceNo, StockCode and CustomerID to text, AmountGBP to fixed decimal, and Month to text.
The YYYY-MM month labels sort chronologically. Add the measures in measures.dax one at a time.

| Page | Visual | Fields |
|---|---|---|
| Sales | KPI cards | Sales GBP, Credits GBP, Net Recorded Sales GBP, Orders |
| Sales | Line chart | Month on X; Sales GBP on Y |
| Sales | Horizontal bar chart | Country on Y; Sales GBP on X; Top 10 by Sales GBP |
| Customers and credits | KPI cards | Average Order Value, Identified Customers, Repeat Customer Share, Credit Value Share |
| Customers and credits | Horizontal bar chart | StockCode on Y; Credits GBP on X; Top 10 by Credits GBP |

Use a Month slicer and a Country slicer. Keep Kind off slicers: measures set that filter themselves.
At the default all-period view, compare the cards against the browser dashboards.
The repeat measure counts orders inside the current selection; a one-month selection asks who ordered twice in that month.

| Measure | Why this calculation? |
|---|---|
| Sales / Credits GBP | CALCULATE separates the two kinds of invoice lines while keeping the month and country filters. |
| Net Recorded Sales | Subtract credits from sales because the import stores credits as positive amounts. This is not profit. |
| Orders | DISTINCTCOUNT counts an invoice once even if it has five products. |
| Average Order Value | Divide total sales by distinct sales orders. Averaging individual lines would answer a different question. |
| Credit Value Share | Divide credited value by sales value. It is not a physical return rate because credits cannot be linked to original orders here. |
| Identified Customers | Exclude blank IDs so anonymous orders do not create a fake customer. |
| Repeat Customers | Test each known customer's order count in the current filter selection. |
| Repeat Customer Share | Divide repeat customers by known buyers, not orders or invoice lines. DIVIDE returns blank when the denominator is zero. |

The included HTML dashboards are browser reports. No .pbix file is included, and the DAX has not been run in Power BI Desktop.
