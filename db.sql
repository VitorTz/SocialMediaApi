CREATE EXTENSION IF NOT EXISTS ltree;
CREATE EXTENSION IF NOT EXISTS citext;

-------------------------------------------------------------------------------

CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,    
    username CITEXT UNIQUE NOT NULL,
    email CITEXT UNIQUE NOT NULL,
    full_name VARCHAR (64) NOT NULL,
    hashed_password CHAR(60) NOT NULL,
    bio TEXT,
    birthdate DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_verified BOOLEAN NOT NULL DEFAULT false,    
    CONSTRAINT users_chk_user_age CHECK (birthdate <= CURRENT_DATE - INTERVAL '16 years'),
    CONSTRAINT users_chk_user_username_length CHECK (LENGTH(username) <= 32),
    CONSTRAINT users_chk_user_email_length CHECK (LENGTH(email) <= 255),
    CONSTRAINT users_chk_user_email_format CHECK (email ~* '^[A-Za-z0-9!#$%&''*+/=?^_`{|}~-]+(?:\.[A-Za-z0-9!#$%&''*+/=?^_`{|}~-]+)*@(?:(?:[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?\.)+[A-Za-z]{2,})$')
);

-------------------------------------------------------------------------------

CREATE TABLE languages (
    code VARCHAR(8) PRIMARY KEY CHECK (code ~ '^[a-z]{2}(-[A-Z]{2})?$'),
    name VARCHAR(64) NOT NULL,
    native_name VARCHAR(64)
);

INSERT INTO  languages 
    (code, name, native_name)
VALUES
    ('zh', 'Chinese', '中文'),
    ('es', 'Spanish', 'Español'),
    ('en', 'English', 'English'),
    ('pt', 'Portuguese', 'Português'),    
    ('ja', 'Japanese', '日本語');

-------------------------------------------------------------------------------

CREATE TYPE 
    post_status_type
AS ENUM  (
    'draft', 
    'published',
    'archived'
);

-------------------------------------------------------------------------------

CREATE TABLE posts (
    post_id SERIAL PRIMARY KEY NOT NULL,
    user_id INTEGER NOT NULL,
    title VARCHAR(256) NOT NULL,
    content TEXT,
    language VARCHAR(8),
    status post_status_type NOT NULL,
    is_pinned BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT posts_fk_user FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
    CONSTRAINT posts_fk_language FOREIGN KEY (language) REFERENCES languages (code)
);
CREATE INDEX idx_posts_user_id ON posts(user_id);
CREATE INDEX idx_posts_language ON posts(language);
CREATE INDEX idx_posts_created_at ON posts(created_at);
CREATE INDEX idx_posts_published ON posts(status) WHERE status = 'published';
CREATE INDEX idx_posts_updated_at ON posts(updated_at);
CREATE INDEX idx_posts_user_status ON posts(user_id, status);

-------------------------------------------------------------------------------

CREATE TABLE post_likes (
    post_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (post_id, user_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (post_id) REFERENCES posts (post_id) ON DELETE CASCADE
) PARTITION BY HASH (post_id);
CREATE TABLE post_likes_0 PARTITION OF post_likes FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE post_likes_1 PARTITION OF post_likes FOR VALUES WITH (MODULUS 4, REMAINDER 1);
CREATE TABLE post_likes_2 PARTITION OF post_likes FOR VALUES WITH (MODULUS 4, REMAINDER 2);
CREATE TABLE post_likes_3 PARTITION OF post_likes FOR VALUES WITH (MODULUS 4, REMAINDER 3);

-------------------------------------------------------------------------------

-- Histórico de post vistos por um usuário
-- Um post é considerado visto quanto o usuário clica para entrar na postagem
CREATE TABLE user_viewed_posts (
    user_id INTEGER NOT NULL,
    post_id INTEGER NOT NULL, 
    viewed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, post_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (post_id) REFERENCES posts (post_id) ON DELETE CASCADE
) PARTITION BY HASH (user_id);
CREATE TABLE user_viewed_posts_0 PARTITION OF user_viewed_posts FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE user_viewed_posts_1 PARTITION OF user_viewed_posts FOR VALUES WITH (MODULUS 4, REMAINDER 1);
CREATE TABLE user_viewed_posts_2 PARTITION OF user_viewed_posts FOR VALUES WITH (MODULUS 4, REMAINDER 2);
CREATE TABLE user_viewed_posts_3 PARTITION OF user_viewed_posts FOR VALUES WITH (MODULUS 4, REMAINDER 3);
CREATE INDEX idx_user_viewed_posts ON user_viewed_posts(user_id, viewed_at DESC);

-------------------------------------------------------------------------------

CREATE TABLE comments (
    comment_id SERIAL PRIMARY KEY NOT NULL,
    user_id INTEGER NOT NULL,
    post_id INTEGER NOT NULL,    
    content TEXT,
    parent_comment_id INTEGER,
    path LTREE,    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,    
    CONSTRAINT comments_fk_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT comments_fk_post FOREIGN KEY (post_id) REFERENCES posts (post_id) ON DELETE CASCADE,
    CONSTRAINT comments_fk_parent FOREIGN KEY (parent_comment_id) REFERENCES comments (comment_id) ON DELETE CASCADE
);
CREATE INDEX idx_comments ON comments (post_id);
CREATE INDEX idx_comments_parent ON comments (parent_comment_id);
CREATE INDEX idx_comments_path ON comments USING GIST (path);

-------------------------------------------------------------------------------

CREATE TABLE comment_likes (
    user_id INTEGER NOT NULL,
    post_id INTEGER NOT NULL,
    comment_id INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(user_id, post_id, comment_id),
    CONSTRAINT comment_likes_fk_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT comment_likes_fk_comment FOREIGN KEY (comment_id) REFERENCES comments(comment_id) ON DELETE CASCADE
) PARTITION BY HASH (post_id);
CREATE TABLE comment_likes_0 PARTITION OF comment_likes FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE comment_likes_1 PARTITION OF comment_likes FOR VALUES WITH (MODULUS 4, REMAINDER 1);
CREATE TABLE comment_likes_2 PARTITION OF comment_likes FOR VALUES WITH (MODULUS 4, REMAINDER 2);
CREATE TABLE comment_likes_3 PARTITION OF comment_likes FOR VALUES WITH (MODULUS 4, REMAINDER 3);
CREATE INDEX idx_comment_likes ON comment_likes (post_id);

-------------------------------------------------------------------------------

CREATE TABLE hashtags (
    hashtag_id SERIAL PRIMARY KEY,
    name CITEXT UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE post_hashtags (
    user_id INTEGER NOT NULL,
    post_id INTEGER NOT NULL,
    hashtag_id INTEGER NOT NULL,
    PRIMARY KEY (user_id, post_id, hashtag_id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT post_hashtags_fk_user FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
    CONSTRAINT post_hashtags_fk_post FOREIGN KEY (post_id) REFERENCES posts (post_id) ON DELETE CASCADE,
    CONSTRAINT post_hashtags_fk_hashtag FOREIGN KEY (hashtag_id) REFERENCES hashtags (hashtag_id) ON DELETE CASCADE
) PARTITION BY HASH (post_id);
CREATE TABLE post_hashtags_0 PARTITION OF post_hashtags FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE post_hashtags_1 PARTITION OF post_hashtags FOR VALUES WITH (MODULUS 4, REMAINDER 1);
CREATE TABLE post_hashtags_2 PARTITION OF post_hashtags FOR VALUES WITH (MODULUS 4, REMAINDER 2);
CREATE TABLE post_hashtags_3 PARTITION OF post_hashtags FOR VALUES WITH (MODULUS 4, REMAINDER 3);

-------------------------------------------------------------------------------

CREATE TYPE metric_type AS ENUM (
    'impressions', 
    'views'    
);

-------------------------------------------------------------------------------

-- Tabela para contagem de métricas de uma postagem
-- Exemplo: (impressions, views)
CREATE TABLE post_metrics (
    post_id INTEGER NOT NULL,
    counter BIGINT NOT NULL DEFAULT 0,    
    type metric_type NOT NULL,
    PRIMARY KEY (post_id, type),
    CONSTRAINT post_metrics_fk_post FOREIGN KEY (post_id) REFERENCES posts (post_id) ON DELETE CASCADE,
    CONSTRAINT post_metrics_chk_positive_counter CHECK (counter >= 0)
) PARTITION BY LIST (type);

CREATE TABLE post_metrics_impressions PARTITION OF post_metrics FOR VALUES IN ('impressions');
ALTER TABLE post_metrics_impressions SET (fillfactor = 80);
CREATE TABLE post_metrics_views PARTITION OF post_metrics FOR VALUES IN ('views');
ALTER TABLE post_metrics_views SET (fillfactor = 80);

-------------------------------------------------------------------------------

-- Tabela para contagem de métricas de um comentário
-- Exemplo: (impressions, views)
CREATE TABLE comment_metrics (
    comment_id INTEGER NOT NULL,
    counter BIGINT NOT NULL DEFAULT 0,
    type metric_type NOT NULL,
    PRIMARY KEY (comment_id, type),
    CONSTRAINT comment_metrics_fk_comment FOREIGN KEY (comment_id) REFERENCES comments (comment_id) ON DELETE CASCADE,
    CONSTRAINT comment_metrics_chk_positive_counter CHECK (counter >= 0)
) PARTITION BY LIST (type);


CREATE TABLE comment_metrics_impressions PARTITION OF comment_metrics FOR VALUES IN ('impressions');
ALTER TABLE comment_metrics_impressions SET (fillfactor = 80);
CREATE TABLE comment_metrics_views PARTITION OF comment_metrics FOR VALUES IN ('views');
ALTER TABLE  comment_metrics_views  SET (fillfactor = 80);

-------------------------------------------------------------------------------

CREATE TABLE direct_conversations (    
    conversation_id SERIAL PRIMARY KEY,
    user1_id INTEGER NOT NULL,
    user2_id INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_interaction_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,    
    UNIQUE (user1_id, user2_id),
    CONSTRAINT direct_conversations_fk_user1 FOREIGN KEY (user1_id) REFERENCES users(user_id),
    CONSTRAINT direct_conversations_fk_user2 FOREIGN KEY (user2_id) REFERENCES users(user_id),
    CONSTRAINT direct_conversations_chk_user_order CHECK (user1_id < user2_id)
);
CREATE INDEX idx_direct_conversations_user1 ON direct_conversations(user1_id);
CREATE INDEX idx_direct_conversations_user2 ON direct_conversations(user2_id);

-------------------------------------------------------------------------------

CREATE TABLE messages (
    message_id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL,
    sender_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reply_to_message_id INTEGER,
    CONSTRAINT messages_fk_conversation_id FOREIGN KEY (conversation_id) REFERENCES direct_conversations(conversation_id) ON DELETE CASCADE,
    CONSTRAINT messages_fk_sender_id FOREIGN KEY (sender_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT messages_fk_reply_to_id FOREIGN KEY (reply_to_message_id) REFERENCES messages(message_id) ON DELETE SET NULL
);
CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_conversation_created ON messages(conversation_id, created_at);

-------------------------------------------------------------------------------

CREATE TABLE message_reads (
    message_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    read_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (message_id, user_id),
    CONSTRAINT message_reads_fk_user_id FOREIGN KEY (user_id) REFERENCES users(user_id),
    CONSTRAINT message_reads_fk_message_id FOREIGN KEY (message_id) REFERENCES messages(message_id) ON DELETE CASCADE
);

-------------------------------------------------------------------------------

CREATE TABLE blocks (
    blocker_id INTEGER NOT NULL,    -- quem está bloqueando
    blocked_id INTEGER NOT NULL,    -- quem está bloqueado
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (blocker_id, blocked_id),
    CONSTRAINT blocks_fk_blocker_id FOREIGN KEY (blocker_id) REFERENCES users(user_id),
    CONSTRAINT blocks_fk_blocked_id FOREIGN KEY (blocked_id) REFERENCES users(user_id),    
    CONSTRAINT blocks_chk_not_self_block CHECK (blocker_id != blocked_id)
) PARTITION BY HASH (blocker_id);
-- Partições (4 tabelas)
CREATE TABLE blocks_0 PARTITION OF blocks FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE blocks_1 PARTITION OF blocks FOR VALUES WITH (MODULUS 4, REMAINDER 1);
CREATE TABLE blocks_2 PARTITION OF blocks FOR VALUES WITH (MODULUS 4, REMAINDER 2);
CREATE TABLE blocks_3 PARTITION OF blocks FOR VALUES WITH (MODULUS 4, REMAINDER 3);
CREATE INDEX idx_blocks_blocker ON blocks (blocker_id);

-------------------------------------------------------------------------------

CREATE TABLE follows (
    follower_id INTEGER NOT NULL, -- quem está seguindo
    followed_id INTEGER NOT NULL, -- quem está sendo seguido
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (follower_id, followed_id),
    CONSTRAINT follows_chk_not_seld_follow CHECK (follower_id != followed_id),
    CONSTRAINT follows_fk_follower FOREIGN KEY (follower_id) REFERENCES users (user_id) ON DELETE CASCADE,
    CONSTRAINT follows_fk_followed FOREIGN KEY (followed_id) REFERENCES users (user_id) ON DELETE CASCADE
) PARTITION BY HASH (follower_id);
CREATE TABLE follows_0 PARTITION OF follows FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE follows_1 PARTITION OF follows FOR VALUES WITH (MODULUS 4, REMAINDER 1);
CREATE TABLE follows_2 PARTITION OF follows FOR VALUES WITH (MODULUS 4, REMAINDER 2);
CREATE TABLE follows_3 PARTITION OF follows FOR VALUES WITH (MODULUS 4, REMAINDER 3);
CREATE INDEX idx_follower ON follows(follower_id);

-------------------------------------------------------------------------------

-- FUNCTIONS AND TRIGGERS

-- Atualiza o campo path
CREATE OR REPLACE FUNCTION set_comment_path()
RETURNS TRIGGER AS $$
DECLARE
    parent_path LTREE;
BEGIN
    -- Verifica se o comment_id já foi atribuído pelo mecanismo SERIAL.
    IF NEW.comment_id IS NULL THEN
        RAISE EXCEPTION 'comment_id não foi atribuído. Verifique a configuração do SERIAL.';
    END IF;
    
    -- Se não houver comentário pai, define o path como o próprio comment_id convertido para LTREE.
    IF NEW.parent_comment_id IS NULL THEN
        NEW.path := NEW.comment_id::text::ltree;
    ELSE
        -- Recupera o path do comentário pai
        SELECT path INTO parent_path FROM comments WHERE comment_id = NEW.parent_comment_id;
        IF parent_path IS NULL THEN
            RAISE EXCEPTION 'O comentário pai com id % não foi encontrado ou não possui path definido.', NEW.parent_comment_id;
        END IF;
        -- Concatena o path do pai com o comment_id do novo comentário
        NEW.path := parent_path || NEW.comment_id::text::ltree;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_set_comment_path
BEFORE INSERT ON comments
FOR EACH ROW
EXECUTE FUNCTION set_comment_path();

-------------------------------------------------------------------------------

-- Retornar um comentário pai e todos seus comentários filhos diretos ou indiretos
-- de forma recursiva
CREATE OR REPLACE FUNCTION get_comment_thread(parent_id INT)
RETURNS JSONB
LANGUAGE plpgsql STABLE AS $$
DECLARE
    parent_path LTREE;
    result JSONB;
BEGIN

    SELECT path INTO parent_path FROM comments WHERE comment_id = parent_id;
    IF parent_path IS NULL THEN
        RETURN NULL;
    END IF;
    
    WITH RECURSIVE comment_tree AS (
        SELECT 
            c.comment_id,
            c.content,
            c.user_id,
            c.post_id,
            c.parent_comment_id,
            c.created_at,
            c.updated_at,
            c.path,
            jsonb_build_object(
                'comment_id', c.comment_id,
                'content', c.content,
                'user_id', c.user_id,
                'post_id', c.post_id,
                'parent_comment_id', c.parent_comment_id,
                'created_at', c.created_at,
                'updated_at', c.updated_at,
                'thread', '[]'::JSONB
            ) AS thread
        FROM 
            comments c
        WHERE 
            c.path = parent_path  -- Comentário raiz

        UNION ALL

        SELECT 
            c.comment_id,
            c.content,
            c.user_id,
            c.post_id,
            c.parent_comment_id,
            c.created_at,
            c.updated_at,
            c.path,
            jsonb_build_object(
                'comment_id', c.comment_id,
                'content', c.content,
                'user_id', c.user_id,
                'post_id', c.post_id,
                'parent_comment_id', c.parent_comment_id,
                'created_at', c.created_at,
                'updated_at', c.updated_at,
                'thread', '[]'::JSONB
            )
        FROM 
            comments c
        JOIN 
            comment_tree ct ON 
            c.parent_comment_id = ct.comment_id
    )
    
    SELECT 
        jsonb_agg(thread) 
    INTO 
        result
    FROM 
        comment_tree
    WHERE 
        path = parent_path;

    RETURN result;
END;
$$;

-------------------------------------------------------------------------------

-- Retornar todos os comentários relacionados a certo post
CREATE OR REPLACE FUNCTION get_post_comments(target_post_id INT)
RETURNS JSONB
LANGUAGE plpgsql STABLE AS $$
DECLARE
    result JSONB;
BEGIN
    WITH RECURSIVE comment_tree AS (
        -- Comentários raiz
        SELECT 
            c.comment_id,
            c.content,
            c.user_id,
            c.post_id,
            c.parent_comment_id,
            c.created_at,
            c.updated_at,
            c.path,
            jsonb_build_object(
                'comment_id', c.comment_id,
                'content', c.content,
                'user_id', c.user_id,
                'post_id', c.post_id,
                'parent_comment_id', c.parent_comment_id,
                'created_at', c.created_at,
                'updated_at', c.updated_at,
                'thread', '[]'::JSONB
            ) AS thread
        FROM 
            comments c
        WHERE 
            c.post_id = target_post_id AND 
            c.parent_comment_id IS NULL  -- Filtra apenas comentários raiz

        UNION ALL
        -- Comentários filhos
        SELECT 
            c.comment_id,
            c.content,
            c.user_id,
            c.post_id,
            c.parent_comment_id,
            c.created_at,
            c.updated_at,
            c.path,
            jsonb_build_object(
                'comment_id', c.comment_id,
                'content', c.content,
                'user_id', c.user_id,
                'post_id', c.post_id,
                'parent_comment_id', c.parent_comment_id,
                'created_at', c.created_at,
                'updated_at', c.updated_at,
                'thread', '[]'::JSONB
            )
        FROM 
            comments c
        JOIN 
            comment_tree ct ON 
            c.parent_comment_id = ct.comment_id
    )

    SELECT 
        jsonb_agg(thread) 
    INTO 
        result
    FROM 
        comment_tree
    WHERE 
        parent_comment_id IS NULL;

    RETURN result;
END;
$$;

-------------------------------------------------------------------------------

-- Garante que o comentário filho pertence ao mesmo post que o comentário pai
CREATE OR REPLACE FUNCTION ensure_same_post() RETURNS TRIGGER AS $$
BEGIN    
    IF (SELECT post_id FROM comments WHERE comment_id = NEW.parent_comment_id) <> NEW.post_id THEN
        RAISE EXCEPTION 'Parent comment must belong to the same post as the child comment.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para chamar a função ensure_same_post ao inserir ou atualizar um comentário
CREATE TRIGGER check_comment_post
BEFORE INSERT OR UPDATE ON comments
FOR EACH ROW
WHEN (NEW.parent_comment_id IS NOT NULL)
EXECUTE FUNCTION ensure_same_post();

-------------------------------------------------------------------------------

-- Manter histórico de posts vistos por cada usuário menor que 40
-- Executada todos os dias as 3:00 de manhã via cron
CREATE OR REPLACE FUNCTION prune_viewed_posts()
RETURNS VOID AS $$
BEGIN
    WITH ranked AS (
        SELECT 
            user_id, 
            post_id,
            row_number() OVER (PARTITION BY user_id ORDER BY viewed_at DESC) AS rn
        FROM user_viewed_posts
    )
    DELETE FROM 
        user_viewed_posts uv
    USING 
        ranked r
    WHERE 
        uv.user_id = r.user_id AND 
        uv.post_id = r.post_id AND 
        r.rn > 40;
END;
$$ LANGUAGE plpgsql;

-------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION get_hashtags_usage(num_days INTEGER)
RETURNS TABLE (
    name CITEXT,
    counter BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        h.name,
        COUNT(*) AS counter
    FROM 
        hashtags h
    JOIN 
        post_hashtags ph ON 
        ph.hashtag_id = h.hashtag_id
    WHERE 
        ph.created_at >= CURRENT_TIMESTAMP - (num_days || ' days')::interval
    GROUP BY 
        h.name
    ORDER BY 
        counter 
    DESC;
END;
$$ LANGUAGE plpgsql;

-------------------------------------------------------------------------------

--Post Metrics
CREATE OR REPLACE FUNCTION get_post_metrics(target_post_id INT)
RETURNS JSONB AS $$
WITH base_metrics AS (
    SELECT COALESCE(
        jsonb_object_agg(m::text, COALESCE(pm.counter, 0)),
        '{}'::jsonb
    ) AS metrics
    FROM unnest(enum_range(NULL::metric_type)) AS m
    LEFT JOIN post_metrics pm 
        ON pm.post_id = target_post_id 
       AND pm.type = m
)
SELECT metrics || jsonb_build_object(
    'comments', (SELECT COUNT(*) FROM comments WHERE post_id = target_post_id),
    'likes',    (SELECT COUNT(*) FROM post_likes WHERE post_id = target_post_id)
)
FROM base_metrics;
$$ LANGUAGE sql STABLE;

-------------------------------------------------------------------------------

-- Comment Metrics
CREATE OR REPLACE FUNCTION get_comment_metrics(target_comment_id INT)
RETURNS JSONB AS $$
WITH base_metrics AS (
    SELECT COALESCE(
        jsonb_object_agg(m::text, COALESCE(cm.counter, 0)),
        '{}'::jsonb
    ) AS metrics
    FROM unnest(enum_range(NULL::metric_type)) AS m
    LEFT JOIN comment_metrics cm 
        ON cm.comment_id = target_comment_id 
       AND cm.type = m
)
SELECT metrics || jsonb_build_object(
    'comments', (SELECT COUNT(*) FROM comments WHERE parent_comment_id = target_comment_id),
    'likes',    (SELECT COUNT(*) FROM comment_likes WHERE comment_id = target_comment_id)
)
FROM base_metrics;
$$ LANGUAGE sql STABLE;