CREATE EXTENSION IF NOT EXISTS ltree;
CREATE EXTENSION IF NOT EXISTS citext;


CREATE TABLE users (
    id SERIAL PRIMARY KEY,    
    username CITEXT UNIQUE NOT NULL,
    email CITEXT UNIQUE NOT NULL,
    full_name VARCHAR (64) NOT NULL,
    bio VARCHAR (2048),
    birthdate DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_verified BOOLEAN DEFAULT false,
    CONSTRAINT chk_user_birthdate CHECK (birthdate < NOW()),
    CONSTRAINT chk_user_username_length CHECK (LENGTH(username) <= 32),
    CONSTRAINT chk_user_email_length CHECK (LENGTH(email) <= 255),
    CONSTRAINT chk_user_email_format CHECK (email ~* '^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$')
);


CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    title VARCHAR(128) NOT NULL,
    content VARCHAR(8096),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);


CREATE TABLE comments (
    id SERIAL PRIMARY KEY,
    content VARCHAR(2048),
    user_id INTEGER NOT NULL,
    post_id INTEGER NOT NULL,
    parent_comment_id INTEGER,
    path LTREE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_post FOREIGN KEY (post_id) REFERENCES posts (id) ON DELETE CASCADE,
    CONSTRAINT fk_parent FOREIGN KEY (parent_comment_id) REFERENCES comments (id) ON DELETE CASCADE
);


CREATE TABLE post_likes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    post_id INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_post_likes_unique_like UNIQUE (user_id, post_id),
    CONSTRAINT fk_post_like_post FOREIGN KEY (post_id) REFERENCES posts (id) ON DELETE CASCADE,
    CONSTRAINT fk_user_line_post FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);


CREATE TABLE comments_likes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    post_id INTEGER NOT NULL, 
    comment_id INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_comment_likes_unique_like UNIQUE (user_id, comment_id),
    CONSTRAINT fk_comment_like_comment FOREIGN KEY (comment_id) REFERENCES comments (id) ON DELETE CASCADE,
    CONSTRAINT fk_comment_like_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT fk_comment_like_post FOREIGN KEY (post_id) REFERENCES posts (id) ON DELETE CASCADE
);


CREATE TABLE followers (
    id SERIAL PRIMARY KEY,
    follower_id INT NOT NULL, -- usuario que esta seguindo
    followed_id INT NOT NULL, -- usuario que esta sendo seguido
    followed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(follower_id, followed_id),
    CONSTRAINT chk_followers_not_self_follow CHECK (follower_id != followed_id),
    CONSTRAINT fk_follower FOREIGN KEY (follower_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT fk_followed FOREIGN KEY (followed_id) REFERENCES users (id) ON DELETE CASCADE
);


CREATE INDEX idx_posts_user_id ON posts(user_id);
CREATE INDEX idx_comments_post_id ON comments(post_id);
CREATE INDEX idx_comments_user_id ON comments(user_id);
CREATE INDEX idx_posts_created_at ON posts (created_at);
CREATE INDEX idx_comments_created_at ON comments (created_at);
CREATE INDEX idx_comments_path_gist ON comments USING GIST (path);


-- Criar uma função para definir automaticamente o campo 'path'
CREATE OR REPLACE FUNCTION set_comment_path()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.parent_comment_id IS NULL THEN
        -- Comentário raiz: definir 'path' como o próprio ID
        NEW.path := NEW.id::TEXT::LTREE;
    ELSE
        -- Comentário filho: concatenar caminho do pai com o ID atual
        NEW.path := (SELECT path FROM comments WHERE id = NEW.parent_comment_id) || NEW.id::TEXT;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- Criar o trigger para chamar a função ao inserir um novo comentário
CREATE TRIGGER trigger_set_comment_path
BEFORE INSERT ON comments
FOR EACH ROW
EXECUTE FUNCTION set_comment_path();

CREATE OR REPLACE FUNCTION get_comment_subtree(_id int) RETURNS jsonb
LANGUAGE sql STABLE AS
$$
    WITH children AS (
    SELECT
        c.id,
        c.content,
        c.user_id,
        c.post_id,
        c.parent_comment_id,
        c.created_at,
        c.updated_at
    FROM comments c
    WHERE c.parent_comment_id = _id
    ORDER BY c.created_at
    )
    SELECT jsonb_agg(
        jsonb_build_object(
            'id', c.id,
            'content', c.content,
            'user_id', c.user_id,
            'post_id', c.post_id,
            'parent_comment_id', c.parent_comment_id,
            'created_at',  TO_CHAR(created_at, 'DD-MM-YYYY HH24:MI:SS'),
            'updated_at',  TO_CHAR(updated_at, 'DD-MM-YYYY HH24:MI:SS'),
            'thread', COALESCE(get_comment_subtree(c.id), '[]'::jsonb)
        )
    )
  FROM children c
$$;


CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER trig_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trig_posts_updated_at
BEFORE UPDATE ON posts
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trig_comments_updated_at
BEFORE UPDATE ON comments
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();