-- =============================================================================
-- 010: añadir columna youtube_live_channel_id a guild_configs
-- =============================================================================
-- Permite a los administradores configurar un canal de Discord independiente
-- para los anuncios de directos de YouTube, separado de los videos.
-- =============================================================================

ALTER TABLE guild_configs
    ADD COLUMN youtube_live_channel_id BIGINT DEFAULT NULL
    AFTER youtube_channel_id;

SELECT 'Migración 010: columna youtube_live_channel_id añadida' AS status;
