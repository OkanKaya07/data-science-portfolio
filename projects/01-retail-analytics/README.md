# Retail sales with Python and SQL

[← All projects](../../README.md#projects) · [Source code](../../sql/retail.sql) · [Results](../../reports/monthly_sales.csv)

**Tools** · Python · pandas · SQLite · Matplotlib

This project follows a retail dataset from invoice lines to monthly sales totals. The main question is how much of a change comes from order volume and how much comes from average order value.

## Step-by-step walkthrough

1. **Audit invoice lines.** I started with 541,909 UCI Online Retail invoice lines. I removed exact duplicates and separated cancellations and nonpositive amounts before calculating positive sales.
2. **Count orders once.** In SQLite, I grouped by month and counted distinct invoice numbers. Counting lines instead would give larger baskets more weight in the order count. [Open the implementation](../../sql/retail.sql#L3-L11).

```sql
WITH monthly AS (
 SELECT substr(InvoiceDate, 1, 7) AS month,
        SUM(Revenue) AS revenue_gbp,
        COUNT(DISTINCT InvoiceNo) AS orders
 FROM sales GROUP BY 1
)
SELECT month, revenue_gbp, orders,
       revenue_gbp / orders AS average_order_value_gbp,
       100.0 * (revenue_gbp / LAG(revenue_gbp) OVER (ORDER BY month) - 1) AS mom_growth_pct
```

<details>
<summary>Open the annotated code screenshot</summary>

![Source walkthrough showing the input, method and exact code excerpt](walkthrough/source.png)

</details>

3. **Inspect the output.** Open [monthly_sales.csv](../../reports/monthly_sales.csv) and the [analysis figure](../../reports/retail_monthly.png). The screenshot puts the saved output beside a short explanation.
4. **Interpret the result.** November 2011 reached £1.50m across 2,769 invoices. December includes only nine days, so the last bar cannot establish a fall in demand.

![Output walkthrough showing measured values and their interpretation](walkthrough/result.png)

## Approach

The source workbook has 541,909 transaction lines. The pipeline audits missing customer identifiers, exact duplicates, nonpositive prices, and negative quantities. It removes exact duplicates, separates negative-quantity transactions, and defines positive sales as positive quantity and price on non-cancellation invoices. Missing customer IDs remain in sales totals.

SQLite queries aggregate invoices into monthly sales, orders, average order value, and month-over-month growth using a CTE and `LAG`. Country-level results reveal geographic concentration. Values are nominal GBP. Positive sales are not profit or accounting net revenue: costs, taxes, matched returns, and adjustments are unavailable. Dropping exact duplicate rows is an explicit assumption; identical legitimate lines could exist.

![Monthly sales](../../reports/retail_monthly.png)

## Deliverables

- [SQL query](../../sql/retail.sql)
- [Monthly KPIs](../../reports/monthly_sales.csv)
- [Country sales](../../reports/country_sales.csv)
- [Cleaning audit](../../reports/retail_audit.json)
- [Measured findings](../../reports/FINDINGS.md)

## Interpretation and next steps

The first and last months also have incomplete customer observation windows. Negative quantities are audited separately and cannot automatically be interpreted as matched refunds. Investigate large orders and non-product stock codes before building a production revenue dashboard. Add product classifications, return matching, and margin data before recommending budget changes.
