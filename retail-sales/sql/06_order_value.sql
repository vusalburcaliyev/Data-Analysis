WITH orders AS (
 SELECT InvoiceNo, SUM(AmountGBP) AS order_gbp
 FROM Transactions WHERE Kind='Sale' GROUP BY InvoiceNo
)
SELECT ROUND(AVG(order_gbp),2) AS average_order_gbp FROM orders;
