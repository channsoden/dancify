DROP TABLE IF EXISTS tags;

CREATE TABLE tags (
  user_id TEXT NOT NULL,
  song_id TEXT NOT NULL,
  tag TEXT NOT NULL
);

CREATE UNIQUE INDEX id ON tags(user_id,song_id,tag);
