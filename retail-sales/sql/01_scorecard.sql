SELECT ROUND(SUM(CASE WHEN Kind='Sale' THEN AmountGBP ELSE 0 END),2) AS sales_gbp,
       ROUND(SUM(CASE WHEN Kind='Credit' THEN AmountGBP ELSE 0 END),2) AS credit_gbp,
       ROUND(SUM(CASE WHEN Kind='Sale' THEN AmountGBP ELSE -AmountGBP END),2) AS net_gbp,
       COUNT(DISTINCT CASE WHEN Kind='Sale' THEN InvoiceNo END) AS orders
FROM Transactions;
