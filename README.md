# NYC Parking Violations Analysis (2000–2025)

**Author:** Jayson Coker  
**Course:** Code:You Data Analytics Capstone  
**Date:** 05/27/2026  

---

# Table of Contents

- [Project Overview](#project-overview)
- [Project Objectives](#project-objectives)
- [Dataset Information](#dataset-information)
- [Technologies Used](#technologies-used)
- [Data Cleaning Process](#data-cleaning-process)
- [Exploratory Data Analysis](#exploratory-data-analysis)
- [Key Findings](#key-findings)
- [Visualizations](#visualizations)
- [How to Run](#how-to-run)
- [Future Improvements](#future-improvements)
- [Conclusion](#conclusion)

---

# Project Overview

This project analyzes **7,056,795 parking violations** issued in New York City from **2000 to 2025**. By merging parking ticket data with fine amount information, the project identifies patterns in parking enforcement, borough revenue distribution, and vehicle demographics.

The analysis focuses on:
- Revenue generated from parking violations
- Borough-level enforcement trends
- Common violation types
- Fine amount distributions
- Relationships between vehicle characteristics and violations

### Total Estimated Revenue
# $434 Million

---

# Project Objectives

The goals of this project were to:

- Clean and merge large-scale datasets
- Perform exploratory data analysis (EDA)
- Identify parking enforcement trends
- Visualize borough-level revenue patterns
- Analyze violation frequency and fine distributions
- Practice data analytics techniques using Python

---

# Dataset Information

## Parking Violations Dataset
- Source: NYC Open Data
- Records: 7+ million
- Years Covered: 2000–2025

## Fine Amount Dataset
- Source: NYC Department of Finance
- Contains violation descriptions and associated fine amounts

---

# Technologies Used

- Python
- Pandas
- NumPy
- Matplotlib
- Seaborn
- Jupyter Notebook

---

# Data Cleaning Process

The raw datasets required extensive cleaning before analysis.

Key cleaning steps included:
- Removing null values
- Standardizing column names
- Converting dates to datetime format
- Merging violation records with fine amounts
- Handling inconsistent borough values
- Filtering invalid records

---

# Exploratory Data Analysis

The analysis explored:
- Revenue totals by borough
- Most common violation types
- Fine amount distributions
- Vehicle year patterns
- Correlations between variables

---

# Key Findings

## Revenue by Borough

![Revenue by Borough](../data/visuals/revenue_by_borough.png)

| Borough | Revenue | Share |
|---------|---------|-------|
| Manhattan | $132.5M | 30.5% |
| Queens | $116.7M | 26.9% |
| Brooklyn | $109.9M | 25.3% |
| Bronx | $58.4M | 13.5% |
| Staten Island | $16.0M | 3.7% |

### Insight
Manhattan generated the highest revenue from parking violations, accounting for over 30% of total estimated revenue.

---

## Fine Amount Distribution

![Box Plot](../data/visuals/fine_distribution_boxplot.png)

### Insight
Median fines ranged from approximately $50 to $115 across boroughs, with Manhattan showing the highest overall median fine amounts.

---

## Top Violations

![Top Violations](../data/visuals/top_violations.png)

### Insight
Bus-related violations carried the highest fines at $515, followed by overnight tractor trailer parking violations at $250.

---

## Correlation Analysis

![Correlation Matrix](../data/visuals/correlation_matrix.png)

### Insight
Weak correlations existed between vehicle year and fine amounts, suggesting that penalties are driven more by violation type than vehicle characteristics.

---

# Visualizations

The project includes:
- Revenue bar charts
- Fine distribution boxplots
- Correlation heatmaps
- Violation frequency charts

---

# How to Run

## Clone the Repository

```bash
git clone <your_repository_url>
cd nyc_parking_analysis
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Launch Jupyter Notebook

```bash
jupyter notebook nyc_parking_analysis.ipynb
```

---

# Future Improvements

Potential future enhancements include:
- Interactive dashboards using Plotly or Tableau
- Geographic heatmaps of violation locations
- Predictive modeling for parking violations
- Time-series forecasting of revenue trends

---

# Conclusion

This project demonstrates the use of Python-based data analytics tools to process and analyze millions of real-world records. The findings reveal significant differences in parking enforcement and revenue generation across New York City boroughs while highlighting the importance of data cleaning and visualization in large-scale analytics projects.