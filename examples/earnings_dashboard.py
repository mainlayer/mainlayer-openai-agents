#!/usr/bin/env python
"""
Earnings Dashboard Example

Demonstrates how to use Mainlayer analytics to track revenue,
monitor resource performance, and understand agent earnings.

Setup:
    export MAINLAYER_API_KEY="ml_..."
    export OPENAI_API_KEY="sk-..."
    python examples/earnings_dashboard.py

This example shows:
- Fetching revenue for different periods
- Understanding transaction patterns
- Monitoring which resources generate income
- Tracking overall profitability
"""

from datetime import datetime
from typing import Any

from mainlayer_openai_agents import MainlayerClient


def print_earnings_dashboard() -> None:
    """
    Display a formatted earnings dashboard with revenue analytics.
    """
    api_key = __import__('os').environ.get('MAINLAYER_API_KEY')
    if not api_key:
        raise ValueError('MAINLAYER_API_KEY environment variable is required')

    client = MainlayerClient(api_key=api_key)

    print('╔════════════════════════════════════════════════════════════╗')
    print('║           MAINLAYER EARNINGS DASHBOARD                     ║')
    print('╚════════════════════════════════════════════════════════════╝\n')

    # -----------------------------------------------------------------------
    # Fetch revenue for different periods
    # -----------------------------------------------------------------------
    periods = ['1d', '7d', '30d', '90d']
    revenue_data: dict[str, Any] = {}

    print('📊 Fetching revenue analytics...\n')

    for period in periods:
        try:
            data = client.get_revenue(period=period)
            revenue_data[period] = data
            print(f'✓ {period.upper():4} — ${data.get("total_revenue_usd", 0):.2f}')
        except Exception as err:
            print(f'⚠️  {period.upper():4} — Error: {err}')

    print()

    # -----------------------------------------------------------------------
    # Display detailed metrics
    # -----------------------------------------------------------------------
    if revenue_data:
        latest_period = revenue_data.get('30d', {})

        print('╔════════════════════════════════════════════════════════════╗')
        print('║                   LAST 30 DAYS METRICS                     ║')
        print('╚════════════════════════════════════════════════════════════╝\n')

        total_revenue = latest_period.get('total_revenue_usd', 0)
        transaction_count = latest_period.get('transaction_count', 0)
        currency = latest_period.get('currency', 'USD')

        print(f'Total Revenue:       ${total_revenue:,.2f} {currency}')
        print(f'Transaction Count:   {transaction_count:,} sales')

        if transaction_count > 0:
            avg_transaction = total_revenue / transaction_count
            print(f'Average Sale Value:  ${avg_transaction:.2f}')
        print()

        # -----------------------------------------------------------------------
        # Resource Performance (if available)
        # -----------------------------------------------------------------------
        breakdown = latest_period.get('breakdown', {})
        if breakdown and isinstance(breakdown, dict):
            print('╔════════════════════════════════════════════════════════════╗')
            print('║              RESOURCE PERFORMANCE BREAKDOWN               ║')
            print('╚════════════════════════════════════════════════════════════╝\n')

            resources = sorted(
                breakdown.items(),
                key=lambda x: x[1].get('revenue', 0),
                reverse=True,
            )

            for idx, (resource_id, metrics) in enumerate(resources[:10], 1):
                resource_revenue = metrics.get('revenue', 0)
                resource_sales = metrics.get('sales', 0)
                resource_name = metrics.get('name', 'Unknown Resource')

                bar_length = int(resource_revenue / max(total_revenue / 30, 1))
                bar = '█' * min(bar_length, 30)

                print(f'{idx:2}. {resource_name[:25]:25} | {bar:30} ${resource_revenue:7.2f}')
                if resource_sales > 0:
                    print(f'    ({resource_sales} sales, ${resource_revenue/resource_sales:.3f} avg)\n')

            print()

        # -----------------------------------------------------------------------
        # Trends & Insights
        # -----------------------------------------------------------------------
        print('╔════════════════════════════════════════════════════════════╗')
        print('║                    TRENDS & INSIGHTS                      ║')
        print('╚════════════════════════════════════════════════════════════╝\n')

        # Compare periods for trend
        one_day = revenue_data.get('1d', {}).get('total_revenue_usd', 0)
        seven_day = revenue_data.get('7d', {}).get('total_revenue_usd', 0)
        thirty_day = revenue_data.get('30d', {}).get('total_revenue_usd', 0)

        if seven_day > 0:
            daily_avg = seven_day / 7
            print(f'Daily Average (7d):  ${daily_avg:.2f}')

        if thirty_day > 0:
            monthly_avg = thirty_day / 30
            print(f'Daily Average (30d): ${monthly_avg:.2f}')

        if one_day > 0 and daily_avg > 0:
            trend = ((one_day - daily_avg) / daily_avg) * 100
            trend_emoji = '📈' if trend > 0 else '📉'
            print(f'Today vs 7d Avg:     {trend_emoji} {trend:+.1f}%')

        print()

        # -----------------------------------------------------------------------
        # Recommendations
        # -----------------------------------------------------------------------
        print('╔════════════════════════════════════════════════════════════╗')
        print('║                   RECOMMENDATIONS                         ║')
        print('╚════════════════════════════════════════════════════════════╝\n')

        if total_revenue < 10:
            print('• Create more resources or increase marketing efforts')
        elif transaction_count < 5:
            print('• Improve resource discovery and pricing')
        else:
            print('• Consider bundling popular resources for upsells')

        if breakdown and len(breakdown) > 1:
            print('• Focus on top-performing resources for optimization')
        else:
            print('• Diversify your resource portfolio')

        print()

    else:
        print('⚠️  No revenue data available. Create resources and sales first.\n')

    # -----------------------------------------------------------------------
    # Footer
    # -----------------------------------------------------------------------
    print('╔════════════════════════════════════════════════════════════╗')
    print(f'Last Updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('Dashboard powered by Mainlayer Analytics')
    print('╚════════════════════════════════════════════════════════════╝')


if __name__ == '__main__':
    print_earnings_dashboard()
