# 01 · Retail sales analytics

**Decision:** Where should a retailer focus performance monitoring and commercial investigation?

## Step-by-step walkthrough

1. **Audit invoice lines.** I started with 541,909 UCI Online Retail invoice lines. I removed exact duplicates and separated cancellations and nonpositive amounts before calculating positive sales.
2. **Count orders once.** In SQLite, I grouped by month and counted distinct invoice numbers. Counting lines instead would give larger baskets more weight in the order count. [Open the implementation](../../sql/retail.sql#L3-L11).

![Source walkthrough showing the input, method and exact code excerpt](walkthrough/source.png)

3. **Inspect the output.** Open [monthly_sales.csv](../../reports/monthly_sales.csv) and the [analysis figure](../../reports/retail_monthly.png). The browser capture below shows values from that artifact.
4. **Interpret the result.** November 2011 reached £1.50m across 2,769 invoices. December includes only nine days, so the last bar cannot establish a fall in demand.

![Output walkthrough showing measured values and their interpretation](walkthrough/result.png)

## What I built

I used pandas to separate cancelled invoices and nonpositive lines before loading sales into SQLite. Of 541,909 source lines, 524,878 qualified as positive sales, totaling £10.64 million. This measures gross positive sales before returns.

```python
    sales = frame[(frame.Quantity > 0) & (frame.UnitPrice > 0) & ~frame.InvoiceNo.str.upper().str.startswith('C')].copy()
```

[See this code in context](../../run.py#L73) · [Inspect the results](../../reports/retail_audit.json)

## Reading the figure

Each bar adds up eligible invoice lines for one month. November 2011 reached £1.50m across 2,769 orders, up 30.6% from October. December’s much shorter bar covers only nine days, so it cannot establish a fall in demand.

[Inspect the underlying result](../../reports/monthly_sales.csv)

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

December 2011 ends on the ninth and must not be treated as a full-month decline. The first and last months also have incomplete customer observation windows. Negative quantities are audited separately and cannot automatically be interpreted as matched refunds. Investigate large orders and non-product stock codes before building a production revenue dashboard. Add product classifications, return matching, and margin data before recommending budget changes.

**Interview discussion:** Why count distinct invoices rather than rows? Why retain anonymous orders in aggregate KPIs? How would you handle a partial month in an executive report?
