FROM apache/airflow:2.7.2

COPY dags/requirements.txt dags/requirements.txt
# RUN PYTHONPATH=/usr/local/lib/python3.8

RUN pip install --user --upgrade pip
RUN pip install --no-cache-dir --user -r dags/requirements.txt 
