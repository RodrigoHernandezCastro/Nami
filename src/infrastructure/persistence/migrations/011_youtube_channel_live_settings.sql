-- =============================================================================
-- 011: añadir columnas para configuración separada de directos en YouTube
-- =============================================================================
-- Arregla columnas faltantes en guild_configs (youtube_channel_id nunca se creó,
-- youtube_live_channel_id referenciaba una columna inexistente).
-- Añade columnas live_* a youtube_channels para mensajes/roles de directos.
-- =============================================================================

-- 1. Arreglar guild_configs
ALTER TABLE guild_configs
    ADD COLUMN IF NOT EXISTS youtube_channel_id BIGINT DEFAULT NULL
    AFTER announcement_channel_id;

ALTER TABLE guild_configs
    ADD COLUMN IF NOT EXISTS youtube_live_channel_id BIGINT DEFAULT NULL
    AFTER youtube_channel_id;

-- 2. Nuevas columnas en youtube_channels para settings específicos de directos
ALTER TABLE youtube_channels
    ADD COLUMN IF NOT EXISTS live_custom_message TEXT DEFAULT NULL
    AFTER custom_message;

ALTER TABLE youtube_channels
    ADD COLUMN IF NOT EXISTS live_mention_type VARCHAR(20) DEFAULT NULL
    AFTER mention_type;

ALTER TABLE youtube_channels
    ADD COLUMN IF NOT EXISTS live_mention_role_ids LONGTEXT DEFAULT NULL
    AFTER mention_role_ids;

SELECT 'Migración 011: columnas live_* añadidas a youtube_channels, columnas faltantes de guild_configs reparadas' AS status;
