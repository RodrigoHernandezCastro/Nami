ALTER TABLE public.youtube_channels 
ADD COLUMN IF NOT EXISTS channel_name VARCHAR(100);

CREATE INDEX IF NOT EXISTS idx_youtube_channel_name 
ON public.youtube_channels(channel_name);


SELECT 'Migración channel_name completada' AS status;