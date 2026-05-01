-- =============================================================================
-- SCHEMA COMPLETO PARA MARIADB
-- Reemplaza todas las migraciones anteriores (001 → 007)
-- Ejecutar SOLO en una base de datos vacía, o con DROP previo
-- =============================================================================

SET NAMES utf8mb4;
SET foreign_key_checks = 0;

-- -----------------------------------------------------------------------------
-- 1. guild_configs
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS guild_configs (
    guild_id                BIGINT          PRIMARY KEY,
    announcement_channel_id BIGINT          DEFAULT NULL,
    streamer_limit          INT             NOT NULL DEFAULT 15,
    default_mention_type    VARCHAR(20)     NOT NULL DEFAULT 'ninguno',
    language                VARCHAR(5)      NOT NULL DEFAULT 'es',
    created_at              TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
                                            ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 2. streamers
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS streamers (
    id                  INT             AUTO_INCREMENT PRIMARY KEY,
    guild_id            BIGINT          NOT NULL,
    username            VARCHAR(50)     NOT NULL,
    custom_message      TEXT            NOT NULL DEFAULT '¡Ya está en vivo!',
    mention_type        VARCHAR(20)     NOT NULL DEFAULT 'ninguno',
    mention_role_ids    LONGTEXT        NOT NULL DEFAULT '[]'
                                        CHECK (JSON_VALID(mention_role_ids)),
    is_online           TINYINT(1)      NOT NULL DEFAULT 0,
    added_at            TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_streamer_guild
        FOREIGN KEY (guild_id) REFERENCES guild_configs(guild_id)
        ON DELETE CASCADE,

    CONSTRAINT uq_streamer_per_guild
        UNIQUE (guild_id, username),

    INDEX idx_streamers_guild_id    (guild_id),
    INDEX idx_streamers_username    (username),
    INDEX idx_streamers_is_online   (is_online)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 3. youtube_channels
--    • channel_name          (migración 006)
--    • last_announced_video_id (migración 004)
--    • announced_video_history (migración 007, era JSONB en PG → LONGTEXT aquí)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS youtube_channels (
    id                          INT             AUTO_INCREMENT PRIMARY KEY,
    guild_id                    BIGINT          NOT NULL,
    channel_id                  VARCHAR(50)     NOT NULL,
    channel_name                VARCHAR(100)    DEFAULT NULL,
    custom_message              TEXT            NOT NULL DEFAULT '¡Nuevo video en YouTube!',
    mention_type                VARCHAR(20)     NOT NULL DEFAULT 'ninguno',
    mention_role_ids            LONGTEXT        NOT NULL DEFAULT '[]'
                                                CHECK (JSON_VALID(mention_role_ids)),
    last_announced_video_id     VARCHAR(20)     DEFAULT NULL,
    announced_video_history     LONGTEXT        NOT NULL DEFAULT '[]'
                                                CHECK (JSON_VALID(announced_video_history)),
    added_at                    TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_youtube_guild
        FOREIGN KEY (guild_id) REFERENCES guild_configs(guild_id)
        ON DELETE CASCADE,

    CONSTRAINT uq_youtube_per_guild
        UNIQUE (guild_id, channel_id),

    INDEX idx_youtube_guild_id      (guild_id),
    INDEX idx_youtube_channel_id    (channel_id),
    INDEX idx_youtube_channel_name  (channel_name),
    INDEX idx_youtube_last_video    (last_announced_video_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET foreign_key_checks = 1;

SELECT 'Schema MariaDB creado correctamente' AS status;
