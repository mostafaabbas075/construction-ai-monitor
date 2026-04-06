import json
import psycopg2
import time
from kafka import KafkaConsumer

# Kafka & Database Configuration
KAFKA_TOPIC = 'excavator_activity'
DB_CONFIG = "host=db dbname=equipment_db user=user password=pass"

def init_db():
    """Continuously attempts to connect to the database until successful."""
    while True:
        try:
            print("[DB] 🔄 Attempting to connect to PostgreSQL...")
            conn = psycopg2.connect(DB_CONFIG)
            cur = conn.cursor()
            
            # Create table matching the required JSON structure
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
            print("✅ Database Connected and Table Ready!")
            return conn, cur
        except Exception as e:
            print(f"❌ Database not ready yet... Retrying in 5s. Error: {e}")
            time.sleep(5)

def start_consuming():
    # 1. Initialize Database Connection
    conn, cur = init_db()

    # 2. Continuously attempt to connect to Kafka
    consumer = None
    while consumer is None:
        try:
            print("[KAFKA] 🔄 Attempting to connect to Kafka...")
            consumer = KafkaConsumer(
                KAFKA_TOPIC, 
                bootstrap_servers=['kafka:29092'],
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='earliest' # Start from the beginning if no offsets exist
            )
            print("✅ Connected to Kafka!")
        except Exception as e:
            print(f"❌ Kafka not ready yet... Retrying in 5s. Error: {e}")
            time.sleep(5)

    print("[INFO] 📥 Consumer started. Waiting for Kafka messages...")
    
    try:
        for message in consumer:
            data = message.value
            
            # Extracting data based on the JSON structure from CV Service
            try:
                frame_id = data.get('frame_id')
                equip_id = data.get('equipment_id')
                ts = data.get('timestamp')
                
                # Nested data extraction
                util_data = data.get('utilization', {})
                state = util_data.get('current_state', 'UNKNOWN')
                activity = util_data.get('current_activity', 'WAITING')
                
                analytics = data.get('time_analytics', {})
                util_pct = analytics.get('utilization_percent', 0.0)

                print(f"[DB] 💾 Saving Frame: {frame_id} | Activity: {activity}")
                
                # Inserting data into PostgreSQL
                cur.execute("""
                    INSERT INTO equipment_logs (frame_id, equipment_id, timestamp_str, state, activity, utilization_percent, raw_payload)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    frame_id, equip_id, ts, state, activity, util_pct, json.dumps(data)
                ))
                conn.commit()
            except Exception as e:
                print(f"⚠️ Error processing payload: {e}")
                conn.rollback()
                
    except KeyboardInterrupt:
        print("🛑 Consumer stopped manually.")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    start_consuming()