ALTER TABLE youtube_channels 
ADD COLUMN IF NOT EXISTS channel_name VARCHAR(100) DEFAULT NULL;

CREATE INDEX IF NOT EXISTS idx_youtube_channel_name 
ON youtube_channels(channel_name);

SELECT 'Migración 006: channel_name añadida' AS status;