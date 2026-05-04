-- =============================================================================
-- 008: cambiar idioma por defecto a 'en' (inglés)
-- =============================================================================
-- Solo cambia el DEFAULT para nuevos guilds. Los guilds ya configurados
-- mantienen su idioma actual; quien quiera moverse a inglés usa /language en.
-- =============================================================================

ALTER TABLE guild_configs
    MODIFY COLUMN language VARCHAR(5) NOT NULL DEFAULT 'en';

SELECT 'Migración 008: idioma por defecto cambiado a en' AS status;