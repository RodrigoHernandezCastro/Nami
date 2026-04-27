
CREATE TABLE IF NOT EXISTS guild_configs (
    guild_id                BIGINT PRIMARY KEY,
    announcement_channel_id BIGINT,
    streamer_limit          INTEGER NOT NULL DEFAULT 15,
    default_mention_type    VARCHAR(20) NOT NULL DEFAULT 'ninguno',
    language                VARCHAR(5)  NOT NULL DEFAULT 'es',
    created_at              TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS streamers (
    id                  SERIAL PRIMARY KEY,
    guild_id            BIGINT NOT NULL,
    username            VARCHAR(50) NOT NULL,
    custom_message      TEXT NOT NULL DEFAULT '¡Ya está en vivo!',
    mention_type        VARCHAR(20) NOT NULL DEFAULT 'ninguno',
    mention_role_ids    JSONB DEFAULT '[]'::jsonb,
    is_online           BOOLEAN NOT NULL DEFAULT FALSE,
    added_at            TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_guild
        FOREIGN KEY (guild_id)
        REFERENCES guild_configs(guild_id)
        ON DELETE CASCADE,

    CONSTRAINT unique_streamer_per_guild
        UNIQUE (guild_id, username)
);

CREATE INDEX IF NOT EXISTS idx_streamers_guild_id ON streamers(guild_id);
CREATE INDEX IF NOT EXISTS idx_streamers_username ON streamers(username);
CREATE INDEX IF NOT EXISTS idx_streamers_is_online ON streamers(is_online);