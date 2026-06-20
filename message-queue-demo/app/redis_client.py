import fakeredis.aioredis

redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
