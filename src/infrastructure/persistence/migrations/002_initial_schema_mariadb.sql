CREATE TABLE IF NOT EXISTS guild_configs (
    guild_id                BIGINT PRIMARY KEY,
    announcement_channel_id BIGINT,
    streamer_limit          INTEGER NOT NULL DEFAULT 15,
    default_mention_type    VARCHAR(20) NOT NULL DEFAULT 'ninguno',
    language                VARCHAR(5)  NOT NULL DEFAULT 'es',
    created_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS streamers (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    guild_id            BIGINT NOT NULL,
    username            VARCHAR(50) NOT NULL,
    custom_message      TEXT NOT NULL,
    mention_type        VARCHAR(20) NOT NULL DEFAULT 'ninguno',
    mention_role_ids    LONGTEXT DEFAULT '[]', 
    is_online           BOOLEAN NOT NULL DEFAULT FALSE,
    added_at            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_guild
        FOREIGN KEY (guild_id)
        REFERENCES guild_configs(guild_id)
        ON DELETE CASCADE,

    CONSTRAINT unique_streamer_per_guild
        UNIQUE (guild_id, username)
);