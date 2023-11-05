CREATE TABLE site_settings (setting_id TEXT NOT NULL PRIMARY KEY, setting_value TEXT NOT NULL);
CREATE TABLE users (user_id BIGSERIAL PRIMARY KEY, name TEXT NOT NULL UNIQUE, password TEXT NOT NULL);
CREATE TABLE topics (topic_id BIGSERIAL PRIMARY KEY, topic TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), created_by BIGINT NOT NULL, upvotes INTEGER NOT NULL DEFAULT 0,CONSTRAINT fk_user FOREIGN KEY(created_by) REFERENCES users(user_id));
CREATE TABLE upvotes (vote_id BIGSERIAL PRIMARY KEY, topic_id BIGINT NOT NULL, user_id BIGINT NOT NULL, CONSTRAINT fk_topic FOREIGN KEY(topic_id) REFERENCES topics(topic_id), CONSTRAINT fk_user FOREIGN KEY(user_id) REFERENCES users(user_id));
CREATE TABLE messages (message_id BIGSERIAL PRIMARY KEY, content TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), topic_id BIGINT NOT NULL, user_id BIGINT NOT NULL, CONSTRAINT fk_topic FOREIGN KEY(topic_id) REFERENCES topics(topic_id), CONSTRAINT fk_user FOREIGN KEY(user_id) REFERENCES users(user_id));
CREATE TABLE private_messages (message_id BIGSERIAL PRIMARY KEY, content TEXT NOT NULL, to_user BIGINT NOT NULL, from_user BIGINT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), read_at TIMESTAMPTZ, CONSTRAINT fk_from_user FOREIGN KEY(from_user) REFERENCES users(user_id), CONSTRAINT fk_to_user FOREIGN KEY(to_user) REFERENCES users(user_id));