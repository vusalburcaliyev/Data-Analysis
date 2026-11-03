WITH monthly AS (
 SELECT Month, ROUND(SUM(AmountGBP),2) AS sales_gbp
 FROM Transactions WHERE Kind='Sale' GROUP BY Month
)
SELECT *, ROUND(100*(sales_gbp/LAG(sales_gbp) OVER (ORDER BY Month)-1),2) AS change_pct
FROM monthly ORDER BY Month;
