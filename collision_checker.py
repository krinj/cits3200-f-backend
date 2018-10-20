# -*- coding: utf-8 -*-

"""
Use this to check BigQuery for colliding keys in the remote table.
"""

from typing import List
from google.cloud import bigquery

__author__ = "Jakrin Juangbhanich"
__email__ = "juangbhanich.k@gmail.com"


def get_existing_keys(
        project: str,
        dataset: str,
        table: str,
        id_list: List[str],
        timestamp_from: int = 0,
        timestamp_to: int = 100000000000
) -> List[str]:
    """ Check the BigQuery table for existing keys that match the query. Returns a list of keys. """
    print("Checking against existing IDs...")
    client = bigquery.Client()

    id_list = tuple(id_list)
    id_string = f"{id_list}"

    # No IDs to check against.
    if len(id_list) == 0:
        return []

    # Remove the comma for SQL.
    if len(id_list) == 1:
        id_string = id_string.replace(",", "")

    # Send a test query to the client.
    query_job = client.query(
        f"""
        SELECT DISTINCT
          submission_id
        FROM
          `{project}.{dataset}.{table}`
        WHERE
          UNIX_SECONDS(timestamp) > {timestamp_from} 
          AND UNIX_SECONDS(timestamp) < {timestamp_to}
          AND submission_id IN {id_string};
        """)

    # Create a sub-list of the responses.
    results = query_job.result()
    existing_ids = [r.submission_id for r in results]
    return existing_ids
