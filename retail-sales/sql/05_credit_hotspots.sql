SELECT StockCode, ROUND(SUM(AmountGBP),2) AS credit_gbp,
       COUNT(DISTINCT InvoiceNo) AS credit_invoices
FROM Transactions WHERE Kind='Credit'
GROUP BY StockCode ORDER BY credit_gbp DESC LIMIT 10;
