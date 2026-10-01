
TOKEN_BUCKET_LUA = """

local key = KEYS[1]

local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local requested = tonumber(ARGV[4])

-- Get the current bucket state.
local data = redis.call(
    "HMGET",
    key,
    "tokens",
    "last_updated"
)

local tokens = tonumber(data[1])
local last_updated = tonumber(data[2])

-- First request: create a full bucket.
if not tokens then
    tokens = capacity
    last_updated = now
else
    -- Calculate how much time has passed.
    local elapsed = now - last_updated

    if elapsed > 0 then
        -- Lazily regenerate tokens.
        tokens = math.min(
            capacity,
            tokens + (elapsed * refill_rate)
        )

        last_updated = now
    end
end

-- Do we have enough tokens?
if tokens >= requested then

    -- Consume tokens.
    tokens = tokens - requested

    -- Save the new state.
    redis.call(
        "HSET",
        key,
        "tokens",
        tokens,
        "last_updated",
        last_updated
    )

    -- Remove inactive buckets after 24 hours.
    redis.call(
        "EXPIRE",
        key,
        21600
    )

    return {1, tostring(tokens)}

else
    -- Not enough tokens.
    return {0, tostring(tokens)}

end

"""
