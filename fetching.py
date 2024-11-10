
import time
import os
import pandas as pd
from SPARQLWrapper import SPARQLWrapper, JSON

import concurrent.futures
from typing import List, Dict
import requests
from ratelimit import limits, sleep_and_retry


#INITIAL FETCH 
def run_initial_sparql_query(query):
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)

    sparql.addCustomHttpHeader(
        'User-Agent', 'MyPaintingDataRetriever/1.0 (jipijipijipi@gmail.com)')
    try:
        results = sparql.query().convert()
    except Exception as e:
        print(f"An error occurred: {e}")
        time.sleep(10)
        results = sparql.query().convert()
    return results


def initial_chunk_list(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def load_or_create_checkpoints(name, target_dir, limit):

    final_file = f'{target_dir}/{name}.csv'

    checkpoint_directory = f'{target_dir}/checkpoints/'

    checkpoint_filename = f'{name}_checkpoint.csv'
    offset_filename = f'{name}_checkpoint_offset.txt'

    checkpoint_path = checkpoint_directory + checkpoint_filename
    offset_path = checkpoint_directory + offset_filename

    if not os.path.exists(checkpoint_directory):
        os.makedirs(checkpoint_directory)

    if os.path.exists(checkpoint_path) and os.path.exists(offset_path):
        data = pd.read_csv(checkpoint_path)
        with open(offset_path, 'r', encoding='utf-8') as f:
            offset = int(f.read())
        batch_number = offset // limit
        print(f"Checkpoint found, resuming {name} from offset {offset}")

    elif os.path.exists(final_file):
        data = pd.read_csv(final_file)
        offset = len(data)
        batch_number = offset // limit
        print(f"Offset : {offset} records from existing {final_file}.")

    else:
        data = pd.DataFrame()
        offset = 0
        batch_number = 0

    return {
        'data': data,
        'offset': offset,
        'batch_number': batch_number,
        'checkpoint_path': checkpoint_path,
        'offset_path': offset_path
    }




def fetch_and_process_wikidata(name, query_template, index_name=None, limit=1000, max_retries=5, checkpoint_interval=2, target_dir='data', max_batches_for_testing=0):

    initial_data = load_or_create_checkpoints(name, target_dir, limit)
    data = initial_data['data']
    offset = initial_data['offset']
    batch_number = initial_data['batch_number']
    checkpoint_path = initial_data['checkpoint_path']
    checkpoint_offset = initial_data['offset_path']

    batch_count = 0

    while True:
        query = query_template.format(limit=limit, offset=offset)
        print(f"Fetching data with OFFSET {offset}")

        results = fetch_results_with_retries(query, max_retries)
        if not results:
            break

        bindings = results['results'].get('bindings', [])
        if not bindings:
            print("No more data returned.")
            break

        data = process_bindings(bindings, data)

        # stop early for testing
        if max_batches_for_testing > 0 and batch_count >= max_batches_for_testing:
            break

        batch_number += 1

        if batch_number % checkpoint_interval == 0:
            save_checkpoint(data, checkpoint_path,
                            checkpoint_offset, offset + limit, batch_number)

        offset += limit
        batch_count += 1
        time.sleep(1)

    print("Fetching complete.")
    if index_name:
        data = data.drop_duplicates(subset=index_name, keep='first')
    data.drop_duplicates(inplace=True)

    export_to_csv(data, name, index_name)

    # Clean up checkpoints
    if os.path.exists(checkpoint_path):
        os.remove(checkpoint_path)
    if os.path.exists(checkpoint_offset):
        os.remove(checkpoint_offset)

    return data


def fetch_results_with_retries(query, max_retries):
    """Fetches SPARQL query results with retry logic."""
    retries = 0
    while retries < max_retries:
        try:
            return run_initial_sparql_query(query)
        except Exception as e:
            print(f"Error: {e}. Retrying ({retries+1}/{max_retries})...")
            retries += 1
            time.sleep(5)
    print("Max retries exceeded. Exiting.")
    return None


def process_bindings(bindings, existing_data):
    """Processes the retrieved bindings and appends to the existing data."""
    processed_data = [
        {
            'item': b['item']['value'],
            'author_wikidata': b.get('author_wikidata', {}).get('value'),
            'location_wikidata': b.get('location_wikidata', {}).get('value')
        }
        for b in bindings
    ]
    df = pd.DataFrame(processed_data)
    return pd.concat([existing_data, df], ignore_index=True)


def save_checkpoint(data, checkpoint_path, checkpoint_offset, offset, batch_number):
    """Saves the data and offset as a checkpoint."""
    data.to_csv(checkpoint_path, index=False)
    with open(checkpoint_offset, 'w', encoding='utf-8') as f:
        f.write(str(offset))
    print(f"Checkpoint saved at batch {batch_number}")


def export_to_csv(df, name, index_name):

    data_directory = 'data/'

    if not os.path.exists(data_directory):
        os.makedirs(data_directory)

    df.to_csv(f'{data_directory}{name}.csv', index=False)
    print(f"Saved to {name}.csv")


#SUPPLEMENTAL FETCH 

# Initialize global session for connection pooling
session = requests.Session()
session.headers.update({
    'User-Agent': 'ArtDataBot/1.0 (jipijipijipi@gmail.com) Python/requests',
    'Accept': 'application/json'
})

@sleep_and_retry
@limits(calls=5, period=1)  # Limit to 5 calls per second
def run_sparql_query(query: str, endpoint_url: str) -> Dict:
    """Execute SPARQL query with rate limiting"""
    response = session.get(
        endpoint_url,
        params={'query': query, 'format': 'json'},
        timeout=30
    )
    response.raise_for_status()
    return response.json()

def process_batch(batch_qids: List[str], endpoint_url: str, query_template: str, src_column_name: str, max_retries: int = 5) -> pd.DataFrame:
    """Process a single batch of QIDs with a customizable SPARQL query template."""
    qid_list_str = ' '.join(f'wd:{qid}' for qid in batch_qids)
    # Insert the QID list and src_column_name into the query template
    batch_query = query_template.format(qid_list=qid_list_str, src_column_name=src_column_name)
    print(batch_query)
    for retry in range(max_retries):
        try:
            results = run_sparql_query(batch_query, endpoint_url)
            bindings = results['results']['bindings']
            
            if not bindings:
                return pd.DataFrame()

            # Dynamically construct data extraction based on available fields
            data = []
            for b in bindings:
                row = {key: b.get(key, {}).get('value') for key in b}
                data.append(row)
            
            return pd.DataFrame(data)
            
        except Exception as e:
            if retry == max_retries - 1:
                print(f"Max retries exceeded: {e}")
                return pd.DataFrame()
            time.sleep(2 ** retry)  # Exponential backoff
    
    return pd.DataFrame()

def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """Split a list into chunks of specified size"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def get_supplement_from_wikidata(name, src_path, src_column_name, query_template: str):
    # Configuration
    endpoint_url = "https://query.wikidata.org/sparql"
    batch_size = 50
    max_workers = 3  # Adjust based on your needs and API limits
    checkpoint_frequency = 10  # Save checkpoint every N batches

    if os.path.exists(f'data/wikidata_{name}.csv'):
        print("Final file already exists. Skipping data retrieval.")
        return

    # Create checkpoint directory if it doesn't exist
    os.makedirs('data/checkpoints', exist_ok=True)

    # Load checkpoint if exists
    checkpoint_file = f'data/checkpoints/{name}_checkpoint.csv'
    batch_index_file = f'data/checkpoints/{name}_batch_index_checkpoint.txt'
    
    if os.path.exists(checkpoint_file) and os.path.exists(batch_index_file):
        detailed_data = pd.read_csv(checkpoint_file)
        with open(batch_index_file, 'r') as f:
            start_batch = int(f.read())
        print(f"Resuming from batch {start_batch}")
    else:
        detailed_data = pd.DataFrame()
        start_batch = 0

    # Read and prepare author data
    basic_data = pd.read_csv(src_path)
    results = basic_data[[src_column_name]].drop_duplicates().reset_index(drop=True)
    results = results.dropna(subset=[src_column_name])  # Drop rows where 'author_wikidata' is NaN
    # Drop values that do not start with 'http://www.wikidata.org/entity'
    results = results[results[src_column_name].str.startswith('http://www.wikidata.org/entity')]
    # Convert item URIs to Q-IDs and create batches
    src_qids = [uri.split('/')[-1] for uri in results[src_column_name].tolist()]
    
    batches = chunk_list(src_qids, batch_size)

    print(f"Processing {len(batches)} batches with {len(src_qids)} records...")

    # Process batches with ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_batch, batch, endpoint_url, query_template, src_column_name): batch_idx 
            for batch_idx, batch in enumerate(batches[start_batch:], start=start_batch)
        }
        
        completed_batches = 0
        for future in concurrent.futures.as_completed(futures):
            batch_idx = futures[future]
            try:
                batch_df = future.result()
                if not batch_df.empty:
                    detailed_data = pd.concat([detailed_data, batch_df], ignore_index=True)
                
                completed_batches += 1
                print(f"Completed batch {batch_idx + 1}/{len(batches)} "
                      f"({(batch_idx + 1)/len(batches)*100:.1f}%)")

                # Save checkpoint periodically
                if completed_batches % checkpoint_frequency == 0:
                    detailed_data.to_csv(checkpoint_file, index=False)
                    with open(batch_index_file, 'w') as f:
                        f.write(str(batch_idx + 1))
                    print(f"Checkpoint saved at batch {batch_idx + 1}")

            except Exception as e:
                print(f"Error processing batch {batch_idx}: {e}")

    # Final processing
    print("Processing complete. Preparing final dataset...")
    detailed_data.drop_duplicates(inplace=True)
    final_data = pd.merge(results, detailed_data, on=src_column_name, how='left')
    
    # Save final results
    final_data.to_csv(f'data/wikidata_{name}.csv', index=False)
    print(f"Data saved to wikidata_{name}.csv")

    # Clean up checkpoints
    if os.path.exists(checkpoint_file):
        os.remove(checkpoint_file)
    if os.path.exists(batch_index_file):
        os.remove(batch_index_file)