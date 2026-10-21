-- Positive sales only. Returns are audited separately by the pipeline.
-- December 2011 is incomplete and must not be compared with full months.
WITH monthly AS (
 SELECT substr(InvoiceDate, 1, 7) AS month,
        SUM(Revenue) AS revenue_gbp,
        COUNT(DISTINCT InvoiceNo) AS orders
 FROM sales GROUP BY 1
)
SELECT month, revenue_gbp, orders,
       revenue_gbp / orders AS average_order_value_gbp,
       100.0 * (revenue_gbp / LAG(revenue_gbp) OVER (ORDER BY month) - 1) AS mom_growth_pct
FROM monthly ORDER BY month;
