from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yaml
import numpy as np
from urllib.parse import urlparse, parse_qs, quote

from scipy import stats
from scipy.stats import pearsonr
from sklearn.preprocessing import MinMaxScaler



def load_config(config_path: str) -> dict:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to YAML configuration file
    
    Returns:
        Dictionary containing configuration settings
    """
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)


def clean_datetime(series: pd.Series, value_type) -> pd.Series:
    """Convert series to datetime format."""
    series = pd.to_datetime(series, errors='coerce')
    if value_type == 'year':
        return pd.to_numeric(series.dt.year, downcast='integer', errors='coerce')
    return series

def clean_categorical(series: pd.Series, categories = None) -> pd.Series:
    """Convert series to categorical format with optional categories."""
    if categories:
        return pd.Categorical(series, categories=categories, ordered=False )
    return series.astype('category')


def extract_wikidata_id(series: pd.Series) -> pd.Series:
    """Extract the Wikidata ID from a series of URLs."""
    return series.str.extract(r'(Q\d+)', expand=False)



def process_column(series: pd.Series, dtype: str, value_type: str = None, categories = None) -> pd.Series:
    """
    Process a single column according to its configuration.
    
    Args:
        series: Column data to process
        dtype: Target data type
        categories: Optional list of categories for categorical data
    
    Returns:
        Processed column data
    """
    if value_type == 'wikidata_url':
        return extract_wikidata_id(series)
    
    if dtype == 'datetime64[ns]':
        return clean_datetime(series, value_type)
    elif dtype == 'category':
        return clean_categorical(series, categories)
    else:
        return series.astype(dtype)


def load_and_process_dataset(
    source_path: str,
    columns_config: dict
) -> pd.DataFrame:
    """
    Load and process a single dataset according to configuration.
    
    Args:
        source_path: Path to source CSV file
        columns_config: Configuration for columns
        dataset_name: Name of the dataset for specific processing
    
    Returns:
        Processed DataFrame
    """
    # Load data
    df = pd.read_csv(source_path)
    
    # Rename columns
    column_mappings = {
        config['original_name']: col_name
        for col_name, config in columns_config.items()
        if 'original_name' in config
    }
    df = df.rename(columns=column_mappings)
    
    # Select configured columns
    df = df[list(columns_config.keys())]
    
    # Process each column
    for column, config in columns_config.items():
        df[column] = process_column(
            df[column],
            config['dtype'],
            config.get('value_type'),
            config.get('categories')
        )
    
    # Set index if specified
    for column, config in columns_config.items():
        if config.get('is_index', False):
            df = df.drop_duplicates(subset=column, keep='first')
            #df = df.set_index(column)
    
    return df

def load_all_datasets(config: dict) -> dict:
    """
    Load and process all datasets defined in configuration.
    
    Args:
        config: Configuration dict
    
    Returns:
        Dictionary of processed DataFrames
    """
    
    return {
        dataset_name: load_and_process_dataset(
            dataset_config['source'],
            dataset_config['columns']
        )
        for dataset_name, dataset_config in config.items()
    }

def get_512px_thumbnail(url):
    """
    Transform a Wikimedia Commons Special:FilePath URL into its 512px thumbnail version.
    
    Args:
        url (str): URL in format: http://commons.wikimedia.org/wiki/Special:FilePath/Filename.jpg
        
    Returns:
        str: The 512px thumbnail URL or None if the URL is null
    
    """
    if not url:
        return None
    
    # Extract the filename from the URL
    filename = url.split('/')[-1]
    
    # Construct the 512px thumbnail URL
    thumbnail_url = f"https://commons.wikimedia.org/w/index.php?title=Special:Redirect/file/{filename}&width=512"
    
    return thumbnail_url


def extract_year(input_str):
    current_year = datetime.now().year
    
    # Check if the input string has at least 4 characters and can be converted to an integer
    if isinstance(input_str, str) and len(input_str) >= 4:
        try:
            year = int(input_str[:4])
            if year > current_year:
                return np.nan
            return year
        except ValueError:
            return np.nan
    return np.nan

def classify_period(decade):
    if decade < 1000:
        return "Antiquity"
    elif 1000 <= decade < 1400:
        return "Medieval"
    elif 1400 <= decade < 1500:
        return "Early Renaissance"
    elif 1500 <= decade < 1600:
        return "High Renaissance and Mannerism"
    elif 1600 <= decade < 1700:
        return "Baroque"
    elif 1700 <= decade < 1780:
        return "Rococo"
    elif 1780 <= decade < 1850:
        return "Neoclassicism and Romanticism"
    elif 1850 <= decade < 1900:
        return "Realism and Impressionism"
    elif 1900 <= decade < 1945:
        return "Modern Art"
    elif 1945 <= decade < 1970:
        return "Post-War and Abstract Expressionism"
    elif 1970 <= decade < 2000:
        return "Contemporary Art"
    else:
        return "Contemporary and Digital Art"