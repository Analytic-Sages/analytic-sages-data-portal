FROM apache/airflow:3.1.5
COPY requirements.txt /
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" -r /requirements.txt
# gcloud SDK for dataproc batches (pipeline needs gcloud dataproc batches submit)
USER root
RUN apt-get update && apt-get install -y curl apt-transport-https gnupg && \
    echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg && \
    apt-get update && apt-get install -y google-cloud-cli && apt-get clean && rm -rf /var/lib/apt/lists/*
USER airflow