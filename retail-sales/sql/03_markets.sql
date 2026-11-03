SELECT Country, ROUND(SUM(AmountGBP),2) AS sales_gbp,
       COUNT(DISTINCT InvoiceNo) AS orders
FROM Transactions WHERE Kind='Sale'
GROUP BY Country ORDER BY sales_gbp DESC LIMIT 10;
