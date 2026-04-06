import json
import psycopg2
from kafka import KafkaConsumer

# Kafka & Database Configuration
KAFKA_TOPIC = 'excavator_activity'
DB_CONFIG = "host=db dbname=equipment_db user=user password=pass"

def init_db():
    conn = psycopg2.connect(DB_CONFIG)
    cur = conn.cursor()
    # Create table matching the required JSON format
    cur.execute("""
        CREATE TABLE IF NOT EXISTS equipment_logs (
            id SERIAL PRIMARY KEY,
            frame_id INT,
            equipment_id TEXT,
            timestamp_str TEXT,
            state TEXT,
            activity TEXT,
            utilization_percent FLOAT,
            raw_payload JSONB
        );
    """)
    conn.commit()
    return conn, cur

def start_consuming():
    conn, cur = init_db()
    consumer = KafkaConsumer(KAFKA_TOPIC, bootstrap_servers=['kafka:29092'],
                             value_deserializer=lambda m: json.loads(m.decode('utf-8')))

    print("[INFO] 📥 Consumer started. Waiting for Kafka messages...")
    for message in consumer:
        data = message.value
        print(f"[DB] Saving frame {data['frame_id']} | Activity: {data['utilization']['current_activity']}")
        
        cur.execute("""
            INSERT INTO equipment_logs (frame_id, equipment_id, timestamp_str, state, activity, utilization_percent, raw_payload)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            data['frame_id'], data['equipment_id'], data['timestamp'],
            data['utilization']['current_state'], data['utilization']['current_activity'],
            data['time_analytics']['utilization_percent'], json.dumps(data)
        ))
        conn.commit()

if __name__ == "__main__":
    start_consuming()