# Food in Art

A data analysis project exploring the representation of food in historical artwork using machine learning and natural language processing techniques.

## Project Overview

This project analyzes a dataset of historical paintings to identify and study the presence of food-related elements across different time periods, cultures, and artistic movements. The analysis combines multiple approaches:

- Natural Language Processing (NLP) for analyzing artwork descriptions
- Computer Vision (CV) using ResNet for image analysis
- Historical economic data correlation analysis

## Data Sources

The project uses the following data sources:
- Wikidata for artwork metadata and images
- Maddison Project Database for historical GDP data
- FastText word embeddings for semantic analysis

## Supports

- Presentation : <https://docs.google.com/presentation/d/1SkXSkEsFx-UF1SlxWeZggwzRyLwRhucVGF-nAMn8vyk/edit#slide=id.p1>
- Dashboard : <https://public.tableau.com/app/profile/jpl.lft/viz/FoodinArt/FoodArt>

## Project Structure

```
project/
│
├── data/                    # Data files and checkpoints
│   ├── checkpoints/        # Temporary processing checkpoints
│   ├── paintings_ids.csv   # Core artwork identifiers
│   └── gdp_pop_decades.csv # Economic indicators
│
├── img/                    # Downloaded artwork images
│   └── img_512/           # 512px thumbnails
│
├── labels/                 # ML training labels
│   └── food_related_keywords.csv
│
├── models/                 # Trained ML models
│   └── best_model_res.pth # Best performing ResNet model
│
└── notebooks/             # Analysis notebooks
    ├── 1_initial_fetch.ipynb
    ├── 2_NLP_labelling.ipynb
    ├── 3_wikimedia_img_downloader.ipynb
    ├── 4_NLP_classification.ipynb
    ├── 5_CV_resnet.ipynb
    ├── 6_food_detection_resnet.ipynb
    └── 7_main.ipynb
```


## Usage

1. **Data Collection**:
   ```bash
   python 1_initial_fetch.ipynb
   ```
   Fetches initial artwork data from Wikidata.

2. **Image Download**:
   ```bash
   python 3_wikimedia_img_downloader.ipynb
   ```
   Downloads artwork images from Wikimedia Commons.

3. **NLP Analysis**:
   ```bash
   python 2_NLP_labelling.ipynb
   python 4_NLP_classification.ipynb
   ```
   Performs food-related keyword analysis and classification.

4. **Computer Vision Analysis**:
   ```bash
   python 5_CV_resnet.ipynb
   python 6_food_detection_resnet.ipynb
   ```
   Trains and applies ResNet model for food detection in images.

5. **Final Analysis**:
   ```bash
   python 7_main.ipynb
   ```
   Combines all analyses and generates final results.

## Model Information

### ResNet Model
- Architecture: ResNet18
- Input size: 224x224 pixels
- Output: 13 food-related categories
- Training data: ~3000 manually labeled images

### NLP Model
- Based on FastText word embeddings
- Vocabulary: ~3000 art-related terms
- Food-related categories: 13 main categories

## Configuration

The project uses a YAML configuration file (`config.yaml`) for managing data processing parameters:
- Data source paths
- Column mappings
- Data type specifications
- Processing parameters

