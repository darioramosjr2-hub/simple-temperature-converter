from enum import Enum
from fastapi import FastAPI, Query
from confluent_kafka import Producer
import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor

DB_HOST = os.getenv('DB_HOST', 'db')
DB_NAME = os.getenv('DB_NAME', 'temp_db')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASS = os.getenv('DB_PASSWORD', 'postgres_password')

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST, database=DB_NAME, 
        user=DB_USER, password=DB_PASS
    )


app = FastAPI(title="Temperature Converter API")

# Configure the Producer to talk to the 'broker' container
conf = {'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'broker:9092')}
topic = os.getenv('KAFKA_TOPIC', 'temperature-conversions')
producer = Producer(conf)


class Unit(str, Enum):
    celsius = "celsius"
    fahrenheit = "fahrenheit"
    kelvin = "kelvin"


def c_to_f(c: float) -> float:
    return c * 9.0 / 5.0 + 32.0


def c_to_k(c: float) -> float:
    return c + 273.15


def f_to_c(f: float) -> float:
    return (f - 32.0) * 5.0 / 9.0


def k_to_c(k: float) -> float:
    return k - 273.15


def convert_value(value: float, from_unit: Unit, to_unit: Unit) -> float:
    # Normalize to Celsius
    if from_unit == Unit.celsius:
        c = value
    elif from_unit == Unit.fahrenheit:
        c = f_to_c(value)
    elif from_unit == Unit.kelvin:
        c = k_to_c(value)
    else:
        raise ValueError("Unsupported unit")

    # Convert Celsius to target
    if to_unit == Unit.celsius:
        return c
    elif to_unit == Unit.fahrenheit:
        return c_to_f(c)
    elif to_unit == Unit.kelvin:
        return c_to_k(c)
    else:
        raise ValueError("Unsupported unit")


@app.get("/")
def read_root():
    return {"message": "Temperature Converter API. Use /convert?value=...&from=...&to=..."}

@app.get("/history")
def get_conversion_history():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Get the last 10 conversion records
        cur.execute("""
            SELECT input_value, input_unit, output_value, output_unit, created_at
            FROM conversions
            ORDER BY created_at DESC
            LIMIT 10
        """)

        history = cur.fetchall()
        cur.close()
        conn.close()
        return history
    except Exception as e:
        return {"error": f"Could not fetch history: {str(e)}"}

@app.get("/convert")
def convert(
    value: float = Query(..., description="numeric temperature value"),
    from_unit: Unit = Query(..., alias="from", description="unit to convert from (celsius|fahrenheit|kelvin)"),
    to_unit: Unit = Query(..., alias="to", description="unit to convert to (celsius|fahrenheit|kelvin)"),
):
    """Convert temperature between Celsius, Fahrenheit and Kelvin."""
    result = convert_value(value, from_unit, to_unit)
    # Return result with reasonable rounding to avoid long floats
    payload = {
        "input": {"value": value, "unit": from_unit},
        "output": {"value": round(result, 6), "unit": to_unit},
    }

    try:
        producer.produce(topic, value=json.dumps(payload).encode('utf-8'))
        producer.flush()
    except Exception as e:
        print(f"Failed to send message to Kafka: {e}")

    return payload


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
