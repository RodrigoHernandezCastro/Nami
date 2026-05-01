ALTER TABLE youtube_channels 
ADD COLUMN IF NOT EXISTS last_announced_video_id VARCHAR(20);

CREATE INDEX IF NOT EXISTS idx_youtube_last_video 
ON youtube_channels(last_announced_video_id);
