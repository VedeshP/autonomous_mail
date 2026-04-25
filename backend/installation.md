

# run command
```uvicorn app.main:app --reload --reload-dir app```


docker-compose up -d
# above commmand will just start docker container 
- 1st time will take time due to downloading image of postgres, spark, kafka, qdrant, etc.


# run command for postgre terminal
```
docker exec -it postgres-db psql -U vedeshp -d mail_db
```

above is my username and database name
    
- exit command - ```exit```

# test user uuid - for me only 
3c1a96ad-d823-481d-846c-03be83909f3a

# alembic - db initialization/migration
```alembic revision --autogenerate -m "Create initial database schema```

```alembic upgrade head```

# spark kafka setup

mkdir -p backend/jars
cd backend/jars

# 1. Download PostgreSQL Driver
```curl -O https://jdbc.postgresql.org/download/postgresql-42.7.3.jar```

# 2. Download Kafka SQL Connectors (must match our Spark version 3.5.1)
```curl -O https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/3.5.1/spark-sql-kafka-0-10_2.12-3.5.1.jar```


```curl -O https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.4.0/kafka-clients-3.4.0.jar```


```curl -O https://repo1.maven.org/maven2/org/apache/commons/commons-pool2/2.11.1/commons-pool2-2.11.1.jar```

```cd ../../ # Go back to root```


# ollama download and setup
```curl -fsSL https://ollama.com/install.sh | sh```

to start ollama in the background
```ollama serve &```

### for nomic embed text - our embedding model
```ollama pull nomic-embed-text```



### running spark
```
/usr/local/spark/bin/spark-submit \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,org.postgresql:postgresql:42.7.3 \
  app/data_pipeline/spark_stream.py
```


### For my reference
Sending token to FastAPI Backend...
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzU0OTQzMjgsInN1YiI6IjEwODBhOTNmLTY4ZGEtNGFhMy05NmUyLTI0Y2Y2NWIxYzE4MCIsInR5cGUiOiJhY2Nlc3MifQ.YoPHXVI5rgSPzF22l8oymkp86IkJUkXtQlBjgzcG66w",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzYwOTczMjgsInN1YiI6IjEwODBhOTNmLTY4ZGEtNGFhMy05NmUyLTI0Y2Y2NWIxYzE4MCIsInR5cGUiOiJyZWZyZXNoIn0.dkV0JJZWsfPnvIYa6ngvHqxLF49nGbTBILndyHB7hUE",
  "token_type": "bearer",
  "user_id": "1080a93f-68da-4aa3-96e2-24cf65b1c180"
}

## test command for gmail authorize

curl -H "Authorization: Bearer <YOUR_JWT_TOKEN>" http://localhost:8000/api/v1/auth/gmail/authorize

### read hdfs 
/usr/local/spark/bin/spark-submit scripts/read_hdfs.py


### topic creation kafka 
```docker exec -it kafka kafka-topics --create --topic raw_emails --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1```


### Clean slate restart stuff - do not do this - do only if you know it is necessary

```
hdfs dfs -rm -r /aethermail/raw_emails/*
```

```
curl -X DELETE http://localhost:6333/collections/emails
```

```
docker exec -it postgres-db psql -U aethermail_user -d aethermail_db -c "TRUNCATE TABLE emails, agent_tasks, action_logs, agent_thoughts CASCADE;"
```


### docker volume 

docker volume ls | grep kafka


### kafka data delete

before run 

```
docker compose down
```
```
docker volume rm backend_kafka_data
```

### delete spark memory 

```
sudo rm -rf /tmp/spark-checkpoints
```

### other delete commands for reset

```
# 1. Stop and remove all containers defined in the file.
docker-compose down

# 2. Delete the NAMED volumes for Kafka and Zookeeper.
docker volume rm backend_kafka_data backend_zookeeper_data backend_zookeeper_log

# 3. Delete the BIND MOUNT folders for Postgres and Qdrant.
# This is why 'docker volume rm' failed before!
sudo rm -rf ./postgres_data
sudo rm -rf ./qdrant_data

# 4. Delete Spark's memory of the Kafka queue.
sudo rm -rf /tmp/spark-checkpoints

# 5. Kill any lingering Ollama process.
pkill ollama
```