# Online retail: from sales to repeat customers

Imagine the shop owner asks: **“Sales look good, but what is left after credits, and are shoppers coming back?”** I used invoice data to answer those questions in order. The goal is a report a shop owner could read and an analyst could check.

[Sales dashboard](Sales_Dashboard.html) · [Customers and credits dashboard](Customers_and_Credits_Dashboard.html) · [Power BI build guide](POWER_BI.md)

Download either HTML dashboard and open it in a browser. The Power BI guide explains how to build the same views with filters.

## First, decide what counts as a sale

The [UCI Online Retail dataset](https://doi.org/10.24432/C5BW33) comes from a UK online retailer. One row is an invoice line, so a single order can appear on several rows. I used December 2010 through November 2011 and left out December 2011 because the source stops on the ninth.

Of 541,909 source lines, 513,921 met the date and value rules. I kept rows with a positive price and nonzero quantity. A cancellation invoice or a negative quantity goes into the credit group; other valid lines count as sales. I kept rows without customer IDs for sales totals and excluded them only from customer counts. I did not drop large orders or identical lines: the file includes wholesale customers and has no unique line ID to tell whether identical lines are accidental duplicates.

## Then, check how sales move

**Gross recorded sales** add up sales lines before credits. **Net recorded sales** subtract the value of credit lines. Neither tells us profit because there are no costs in the dataset.

The [monthly query](sql/02_monthly_sales.sql) adds up sales for each month before using `LAG` to look at the previous month's total:

```sql
WITH monthly AS (
  SELECT Month, SUM(AmountGBP) AS sales_gbp
  FROM Transactions
  WHERE Kind = 'Sale'
  GROUP BY Month
)
SELECT Month, sales_gbp,
       LAG(sales_gbp) OVER (ORDER BY Month) AS previous_month
FROM monthly;
```

I grouped first so the comparison is between two months, not two invoice lines. The first month has no previous month in this study. The [market query](sql/03_markets.sql) then shows which countries account for the most sales.

## Next, ask who came back

A **repeat customer** is a known customer ID with at least two distinct sales invoices in the period. Buying several products on one invoice still counts as one order.

```sql
SELECT CustomerID, COUNT(DISTINCT InvoiceNo) AS orders
FROM Transactions
WHERE Kind = 'Sale' AND CustomerID IS NOT NULL
GROUP BY CustomerID;
```

The [full repeat query](sql/04_customer_repeat.sql) counts customers with two or more orders and divides by the number of identified buyers. This tells us how many buyers came back within the period, not whether they stayed loyal afterward.

## What the numbers said

| Metric | Result |
|---|---:|
| Gross recorded sales | £10,027,891.86 |
| Recorded credits | £691,687.82 |
| Net recorded sales | £9,336,204.04 |
| Sales invoices | 19,141 |
| Average sales invoice | £523.90 |
| Known buyers who ordered again | 2,759 of 4,297 (64.21%) |

The UK accounted for about 84% of gross recorded sales. Credits were about 6.9% of gross recorded sales. The two largest credit codes were AMAZONFEE and M, so the next step is to separate fees and manual entries from merchandise before drawing product conclusions.

## Finally, decide what to investigate

Start with the codes carrying the largest credited value. Some codes represent fees or adjustments rather than products. The [credit query](sql/05_credit_hotspots.sql) groups by product code so the same product can be counted together even if the description varies. High credited value could reflect higher sales or a few large adjustments. Check the original invoices before treating it as a product problem.

I also included [the scorecard](sql/01_scorecard.sql) and [average order value](sql/06_order_value.sql). The order-value query adds up each invoice before taking the average, so large baskets with more lines don't get extra weight.

## Why use DAX as well?

SQL produced the checked totals in the browser dashboards. DAX lets the Power BI measures recalculate when a viewer selects a country or month.

```dax
Average Order Value = DIVIDE([Sales GBP], [Orders])
```

I used a ratio of two measures so both react to the same filters. If the selection has no orders, DIVIDE gives a blank instead of a division error. [Every measure is explained in the Power BI guide.](POWER_BI.md)

## Run it again

1. Download and unzip the workbook from [UCI](https://archive.ics.uci.edu/dataset/352/online+retail).
2. Run `python -m pip install -r requirements.txt`.
3. Run `python build.py "Online Retail.xlsx"` from this directory.

The script builds the dashboards and the CSV for Power BI, then checks that monthly totals add up and that gross sales minus credits equals net recorded sales.

Data: Daqing Chen (2015), *Online Retail*, UCI Machine Learning Repository, CC BY 4.0. This project filters and summarizes the original data.
