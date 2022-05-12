import datetime
import json
import time
from builtins import range
from datetime import timedelta

from airflow.models import DAG
from airflow.utils.dates import days_ago
from airflow.operators.http_operator import SimpleHttpOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.operators.python import PythonOperator
from airflow.models import Variable

args = {
    'start_date': days_ago(2),
    'provide_context': True,
    'owner': 'Nikita Anshakov',
    'depends_on_past': False,
    'retries': 0,
    'retry_delay': timedelta(minutes=5)
}

dag = DAG(
    dag_id='exchange_loader_hist',
    default_args=args,
    schedule_interval='@once',
    tags=['yandex']
)
from_dt = datetime.datetime.strptime(Variable.get("from_dt"), '%Y-%m-%d')
to_dt = datetime.datetime.strptime(Variable.get("to_dt"), '%Y-%m-%d')
step = datetime.timedelta(days=1)

while from_dt <= to_dt:
    dt_to_print = from_dt.strftime('%Y%m%d')
    exchange = SimpleHttpOperator(
        task_id=f"get_exchange_data_{dt_to_print}",
        method='GET',
        http_conn_id='http_exchangerate',
        endpoint=from_dt.strftime('%Y-%m-%d') + '?base={{ var.value.base }}&symbols={{ var.value.symbols }}',
        headers={"Content-Type": "application/json"},
        dag=dag)


    def parse_price(**context):
        json_data = json.loads(context['ti'].xcom_pull(task_ids=f"get_exchange_data_{context['dt_to_print']}", key='return_value'))
        context['ti'].xcom_push("ts", json_data['date'])
        return int(json_data['rates']['USD'] * 1_000_000)


    parse = PythonOperator(
        task_id=f"parse_{dt_to_print}",
        python_callable=parse_price,
        provide_context=True,
        op_kwargs={'dt_to_print': dt_to_print},
        dag=dag)

    insert = PostgresOperator(
        task_id=f"insert_{dt_to_print}",
        postgres_conn_id='postgres_default',
        sql="INSERT INTO public.{{ var.value.pg_table }} "
            f"VALUES ('{{{{ var.value.base }}}}/{{{{ var.value.symbols }}}}', '{{{{ task_instance.xcom_pull(task_ids='parse_{dt_to_print}', key='ts') }}}}', {{{{ task_instance.xcom_pull(task_ids='parse_{dt_to_print}', key='return_value') }}}});",
        dag=dag)

    exchange >> parse >> insert
    from_dt += step

if __name__ == "__main__":
    dag.cli()
