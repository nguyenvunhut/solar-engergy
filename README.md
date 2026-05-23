# Outlier Detection in High-School Network Monitoring

A data analysis project for detecting outliers in monitoring systems using machine learning techniques.

## Project Overview

This project focuses on developing methods to identify anomalies and outliers in network monitoring data. It includes data collection, preprocessing, and analysis pipelines to support outlier detection research.

## Project Structure

```
datn_outlier_hs_nlmt/
├── ultils/
│   └── Crawl_data.ipynb    # Data collection from NASA Power API
└── README.md               # This file
```

## Components

### Data Collection (`ultils/Crawl_data.ipynb`)

This Jupyter notebook handles data collection from the NASA Power API, gathering solar radiation and weather parameters across multiple geographic locations. The collected data includes:

- **Solar Radiation**: All-sky and clear-sky surface shortwave radiation
- **Precipitation**: Corrected precipitation data
- **Temperature**: Surface temperature measurements

## Requirements

- Python 3.x
- pandas
- requests
- jupyter

## Getting Started

1. Clone or download this repository
2. Install the required dependencies:
   ```bash
   pip install pandas requests jupyter
   ```
3. Open and run the notebooks:
   ```bash
   jupyter notebook ultils/Crawl_data.ipynb
   ```

## Data Source

The project uses the [NASA POWER API](https://power.larc.nasa.gov/) for meteorological and solar data collection.

## Authors & Contributors

- FPT Polytechnic - Semester 6 Project

## Notes

- Ensure you have internet access to fetch data from NASA APIs
- Adjust date ranges and geographic coordinates as needed in the notebooks
- Store collected data appropriately for subsequent analysis phases

## License

This project is for educational purposes.
For academic use only.
