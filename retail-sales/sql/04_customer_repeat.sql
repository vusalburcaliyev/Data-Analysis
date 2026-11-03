WITH customers AS (
 SELECT CustomerID, COUNT(DISTINCT InvoiceNo) AS orders
 FROM Transactions WHERE Kind='Sale' AND CustomerID IS NOT NULL GROUP BY CustomerID
)
SELECT COUNT(*) AS identified_customers,
       SUM(CASE WHEN orders>=2 THEN 1 ELSE 0 END) AS repeat_customers,
       ROUND(100.0*AVG(CASE WHEN orders>=2 THEN 1 ELSE 0 END),2) AS repeat_pct
FROM customers;
