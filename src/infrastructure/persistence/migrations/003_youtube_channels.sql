-- MariaDB Teramont — YouTube Channels Completo
CREATE TABLE IF NOT EXISTS youtube_channels (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    guild_id            BIGINT NOT NULL,
    channel_id          VARCHAR(50) NOT NULL,
    channel_name        VARCHAR(100),
    custom_message      TEXT NOT NULL DEFAULT '¡Nuevo video en YouTube!',
    mention_type        VARCHAR(20) NOT NULL DEFAULT 'ninguno',
    mention_role_ids    LONGTEXT DEFAULT '[]',
    last_announced_video_id VARCHAR(20) DEFAULT NULL,
    added_at            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_youtube_guild
        FOREIGN KEY (guild_id) REFERENCES guild_configs(guild_id) ON DELETE CASCADE,
    CONSTRAINT unique_youtube_per_guild
        UNIQUE (guild_id, channel_id),

    INDEX idx_youtube_guild_id (guild_id),
    INDEX idx_youtube_channel_id (channel_id),
    INDEX idx_youtube_channel_name (channel_name),
    INDEX idx_youtube_last_video (last_announced_video_id)
);