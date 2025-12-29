from confluent_kafka import Consumer, KafkaError
import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
import time

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'db'),
        database=os.getenv('DB_NAME', 'temp_db'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'postgres_password'),
        connect_timeout=10
    )

def init_db():
    retries = 5
    while retries > 0:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversions (
                    id SERIAL PRIMARY KEY,
                    input_value FLOAT NOT NULL,
                    input_unit VARCHAR(20) NOT NULL,
                    output_value FLOAT NOT NULL,
                    output_unit VARCHAR(20) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            cursor.close()
            conn.close()
            print("Database initialized successfully.", flush=True)
            return
        except psycopg2.OperationalError as e:
            retries -= 1
            print(f"Database connection failed. Retrying... ({5 - retries}/5)", flush=True)
            time.sleep(5)
    raise Exception("Failed to connect to the database after multiple attempts.")

print("Starting Kafka consumer...")

KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'broker:9092')
TOPIC_NAME = os.getenv('KAFKA_TOPIC', 'temperature-conversions')
GROUP_ID = os.getenv('KAFKA_CONSUMER_GROUP', 'temperature-conversions-group')

conf = {
    'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
    'group.id': GROUP_ID,
    'auto.offset.reset': 'earliest'
}

consumer = Consumer(conf)
consumer.subscribe([TOPIC_NAME])

print(f"Consumer Started. Monitoring topic: {TOPIC_NAME}", flush=True)

init_db()

try:
    while True:
        msg = consumer.poll(1.0)  # Timeout of 1 second

        if msg is None:
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                continue
            else:
                print(f"Consumer Error: {msg.error()}", flush=True)
                continue

        try:
            raw_data = msg.value().decode('utf-8')
            data = json.loads(raw_data)

            input_value = data['input']['value']
            output_value = data['output']['value']

            conn = get_db_connection()
            cursor = conn.cursor()
            insert_query = """
            INSERT INTO conversions (input_value, input_unit, output_value, output_unit)
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(insert_query, (
                data['input']['value'],
                data['input']['unit'],
                data['output']['value'],
                data['output']['unit']
            ))

            conn.commit()
            cursor.close()
            conn.close()

            print(f"Record saved to Database", flush=True)

            print(f"Received event: {input_value} -> {output_value}", flush=True)
        except json.JSONDecodeError as e:
            print(f"POISON PILL: Received non-JSON data: {msg.value()}", flush=True)
        except KeyError as e:
            print(f"MISSING DATA: Message was missing field {e}. Data: {raw_data}", flush=True)
        except Exception as e:
            print(f"UNKOWN ERROR: {e}. Data: {raw_data}", flush=True)
finally:
    print("Shutting down consumer...", flush=True)
    consumer.close()