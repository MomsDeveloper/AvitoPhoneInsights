from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime

def run_parser():
    import data_parser as dp
    print("Parsing the page...")
    dp.parse_data()

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
}

with DAG(
    'parse_dag',
    default_args=default_args,
    description='A DAG to parse data from Avito',
    schedule_interval=None,
    catchup=False,
) as dag:

    execute_parser = PythonOperator(
        task_id='run_parser',
        python_callable=run_parser,
    )
