import datetime
import json
from datetime import timedelta

from airflow.models import DAG
from airflow.operators.http_operator import SimpleHttpOperator
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.utils.dates import days_ago

args = {
    'start_date': days_ago(2),
    'provide_context': True,
    'owner': 'Nikita Anshakov',
    'depends_on_past': False,
    'retries': 0,
    'retry_delay': timedelta(minutes=5)
}

dag = DAG(
    dag_id='exchange_loader',
    default_args=args,
    schedule_interval='0 */3 * * *',
    tags=['yandex']
)

exchange = SimpleHttpOperator(
    task_id='get_exchange_data',
    method='GET',
    http_conn_id='http_exchangerate',
    endpoint='/latest?base={{ var.value.base }}&symbols={{ var.value.symbols }}',
    headers={"Content-Type": "application/json"},
    dag=dag)


def parse_price(**context):
    json_data = json.loads(context['ti'].xcom_pull(task_ids='get_exchange_data', key='return_value'))
    context['ti'].xcom_push("ts", json_data['date'])
    return int(json_data['rates']['USD'] * 1_000_000)


parse = PythonOperator(
    task_id='parse',
    python_callable=parse_price,
    provide_context=True,
    dag=dag)

insert = PostgresOperator(
    task_id='insert',
    postgres_conn_id='postgres_default',
    sql="INSERT INTO public.{{ var.value.pg_table }} "
        "VALUES ('{{ var.value.base }}/{{ var.value.symbols }}', '{{ task_instance.xcom_pull(task_ids='parse', key='ts') }}', {{ task_instance.xcom_pull(task_ids='parse', key='return_value') }});",
    dag=dag)

exchange >> parse >> insert

if __name__ == "__main__":
    dag.cli()
