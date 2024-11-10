
# Food in Art

## Project Overview

The **Food in Art** project is an exploration of how food appears in artworks throughout different periods and its potential correlations with socio-economic factors like GDP and population. Using data processing and visualization tools, the project analyzes patterns and correlations between the depiction of food and historical context.

## Objectives

- Identify and analyze artworks that contain food elements using various datasets.
- Explore correlations between the prevalence of food-related artworks and socio-economic indicators.
- Create visualizations to highlight key trends and relationships across different historical periods.

## Key Features

- **Data Loading and Processing**: Configurable dataset loading through YAML configuration, with data cleaning functions to handle datetime, categorical, and Wikidata URL extraction.
- **Dataset Merging**: Combining multiple datasets, including artwork metadata, locations, authors, and food-related data, to form a comprehensive analysis dataset.
- **Correlation Analysis**: Statistical analysis to explore correlations between food depiction and normalized socio-economic data (e.g., GDP per capita).
- **Data Normalization**: Using MinMaxScaler to normalize GDP and population data for comparative analysis.

## Data Sources

- **Artwork Data**: Includes metadata such as painting titles, authors, creation dates, and locations.
- **Food Data**: Contains information about food detected in artworks through word associations and image analysis.
- **Socio-Economic Data**: GDP and population data per decade.

## How to Use

1. **Configuration**: Modify the `config.yaml` file to specify dataset paths and column configurations.
2. **Data Loading**: Load and process datasets using the provided functions.
3. **Data Analysis**: Use the merged dataset to perform statistical analyses and generate visualizations.
4. **Export**: Export processed data for further analysis or machine learning applications.



