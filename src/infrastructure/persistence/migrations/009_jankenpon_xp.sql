-- 009_jankenpon_xp.sql
-- Sistema de XP para el comando !jankenpon.
-- Una fila por (user_id, guild_id). El leaderboard global se calcula
-- vía SUM(xp) GROUP BY user_id; los índices están dimensionados para eso.

CREATE TABLE IF NOT EXISTS user_xp (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    user_id       BIGINT NOT NULL,
    guild_id      BIGINT NOT NULL,
    xp            INT NOT NULL DEFAULT 0,
    games_played  INT NOT NULL DEFAULT 0,
    wins          INT NOT NULL DEFAULT 0,
    losses        INT NOT NULL DEFAULT 0,
    draws         INT NOT NULL DEFAULT 0,
    updated_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                  ON UPDATE CURRENT_TIMESTAMP,

    -- Garantiza una sola fila por (usuario, servidor).
    UNIQUE KEY uq_user_guild (user_id, guild_id),

    -- Para el leaderboard por servidor: ORDER BY xp DESC WHERE guild_id = ?
    INDEX idx_user_xp_guild (guild_id, xp DESC),

    -- Para el leaderboard global: GROUP BY user_id agrega rápido con este índice.
    INDEX idx_user_xp_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;