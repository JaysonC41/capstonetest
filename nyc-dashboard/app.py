import pandas as pd
from dash import Dash, dcc, html
import plotly.express as px

from queries import (
    get_precinct_summary,
    get_monthly_trends,
    get_top_violations,
    get_revenue_by_precinct
)

# ----------------------------
# LOAD AGGREGATED DATA ONLY
# ----------------------------
precinct = pd.DataFrame(get_precinct_summary(), columns=["precinct", "tickets"])
monthly = pd.DataFrame(get_monthly_trends(), columns=["month", "tickets"])
violations = pd.DataFrame(get_top_violations(), columns=["violation", "count"])
revenue = pd.DataFrame(get_revenue_by_precinct(), columns=["precinct", "revenue"])

# ----------------------------
# CHARTS
# ----------------------------
fig_precinct = px.bar(precinct, x="precinct", y="tickets", title="Tickets by Precinct")
fig_month = px.line(monthly, x="month", y="tickets", title="Monthly Ticket Trends")
fig_violations = px.bar(violations, x="count", y="violation", orientation="h", title="Top Violations")
fig_revenue = px.bar(revenue, x="precinct", y="revenue", title="Estimated Revenue by Precinct")

# ----------------------------
# APP
# ----------------------------
app = Dash(__name__)

app.layout = html.Div([
    html.H1("NYC Parking Violations Dashboard"),

    dcc.Graph(figure=fig_precinct),
    dcc.Graph(figure=fig_month),
    dcc.Graph(figure=fig_violations),
    dcc.Graph(figure=fig_revenue),
])

if __name__ == "__main__":
    app.run_server(debug=True)