# Online retail: from sales to repeat customers

## Introduction

Imagine the shop owner asks: **“Sales look good, but what is left after credits, and are shoppers coming back?”** I used invoice data to answer those questions in order. The goal is a report a shop owner could read and an analyst could check.

[Power BI report](power-bi/) · [SQL queries](sql/)

The [Power BI project](power-bi/) includes two pages for sales, credits, and repeat buyers. Download and extract the repository ZIP, open `retail-sales/power-bi/OnlineRetail.pbip` in Power BI Desktop, and select **Refresh**.

## Background

### What I counted as a sale

The [UCI Online Retail dataset](https://doi.org/10.24432/C5BW33) comes from a UK online retailer. One row is an invoice line, so a single order can appear on several rows. I used December 2010 through November 2011 and left out December 2011 because the source stops on the ninth.

Of 541,909 source lines, 513,921 met the date and value rules. I kept rows with a positive price and nonzero quantity. A cancellation invoice or a negative quantity goes into the credit group; other valid lines count as sales. I kept rows without customer IDs for sales totals and excluded them only from customer counts. I did not drop large orders or identical lines: the file includes wholesale customers and has no unique line ID to tell whether identical lines are accidental duplicates.

### The Questions Answered:

1. How much did the retailer record in gross sales and after credits?
2. How many identified buyers ordered again?
3. Where were sales and credits concentrated?

## Tools

- **SQL and SQLite:** I calculated sales, order value, repeat buying and credits.
- **Python:** I prepared the workbook and checked the totals.
- **Power BI and DAX:** I built an editable report for sales, credits, and repeat buying.

## Analysis

### 1. Gross sales and credits

I found £10.03 million in gross recorded sales and £691,688 in credits, leaving £9.34 million in net recorded sales.

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

### 2. Identified buyers who ordered again

I found that 2,759 of 4,297 identified buyers (64.21%) placed at least two distinct sales invoices during the year.

A **repeat customer** is a known customer ID with at least two distinct sales invoices in the period. Buying several products on one invoice still counts as one order.

```sql
SELECT CustomerID, COUNT(DISTINCT InvoiceNo) AS orders
FROM Transactions
WHERE Kind = 'Sale' AND CustomerID IS NOT NULL
GROUP BY CustomerID;
```

The [full repeat query](sql/04_customer_repeat.sql) counts customers with two or more orders and divides by the number of identified buyers. This tells us how many buyers came back within the period, not whether they stayed loyal afterward.

### Findings

| Metric | Result |
|---|---:|
| Gross recorded sales | £10,027,891.86 |
| Recorded credits | £691,687.82 |
| Net recorded sales | £9,336,204.04 |
| Sales invoices | 19,141 |
| Average sales invoice | £523.90 |
| Known buyers who ordered again | 2,759 of 4,297 (64.21%) |

The UK accounted for about 84% of gross recorded sales. Credits were about 6.9% of gross recorded sales. The two largest credit codes were AMAZONFEE and M, so the next step is to separate fees and manual entries from merchandise before drawing product conclusions.

### 3. Where sales and credits were concentrated

Start with the codes carrying the largest credited value. Some codes represent fees or adjustments rather than products. The [credit query](sql/05_credit_hotspots.sql) groups by product code so the same product can be counted together even if the description varies. High credited value could reflect higher sales or a few large adjustments. Check the original invoices before treating it as a product problem.

I also included [the scorecard](sql/01_scorecard.sql) and [average order value](sql/06_order_value.sql). The order-value query adds up each invoice before taking the average, so large baskets with more lines don't get extra weight.

### Why I used DAX

I used SQL to check the totals and DAX to recalculate sales and order metrics when a viewer selects a country or month.

```dax
Average invoice value = DIVIDE([Gross sales], [Sales invoices])
```

I used a ratio of two measures so both react to the same filters. If the selection has no orders, DIVIDE gives a blank instead of a division error.

## Run it again

1. Download and unzip the workbook from [UCI](https://archive.ics.uci.edu/dataset/352/online+retail).
2. Run `python -m pip install -r requirements.txt`.
3. Run `python build.py "Online Retail.xlsx"` from this directory.

The script rebuilds the analysis, exports the CSV, and checks that monthly totals add up and that gross sales minus credits equals net recorded sales. The Power BI project embeds the checked summary tables.

Data: Daqing Chen (2015), *Online Retail*, UCI Machine Learning Repository, CC BY 4.0. This project filters and summarizes the original data.
