# nexsovereign-architecture
System architecture, API specifications, and Docker deployment stack for the NexSovereign IIoT Pipeline Monitoring MVP.
nexsovereign-backend/
├── docker-compose.yml
├── mosquitto/
│   └── config/
│       └── mosquitto.conf
├── database/
│   └── init.sql
├── app/
│   ├── init.py
│   ├── main.py
│   ├── config.py
│   ├── db.py
│   ├── models.py
│   ├── schemas.py
│   ├── mqtt_client.py
│   └── websocket_manager.py
└── requirements.txt
