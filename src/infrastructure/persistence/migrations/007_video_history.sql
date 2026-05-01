ALTER TABLE youtube_channels 
ADD COLUMN IF NOT EXISTS announced_video_history JSONB DEFAULT '[]'::jsonb;

-- Índice GIN para queries JSONB
CREATE INDEX IF NOT EXISTS idx_youtube_history 
ON youtube_channels USING GIN(announced_video_history);

-- Migrar datos existentes (opcional)
UPDATE youtube_channels 
SET announced_video_history = jsonb_build_array(last_announced_video_id)
WHERE last_announced_video_id IS NOT NULL;

SELECT 'Migración video_history completada' AS status;