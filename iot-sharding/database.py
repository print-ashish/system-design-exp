import asyncpg

# Define the connection strings for our shards
SHARDS = {
    0: "postgresql://admin:password@localhost:5431/iot_shard_1",
    1: "postgresql://admin:password@localhost:5432/iot_shard_2",
    2: "postgresql://admin:password@localhost:5433/iot_shard_3"
}

def get_shard_url(device_id: int):
    # Modular Sharding logic
    shard_index = device_id % 3
    return SHARDS[shard_index]

async def get_shard_conn(device_id: int):
    url = get_shard_url(device_id)
    return await asyncpg.connect(url)
