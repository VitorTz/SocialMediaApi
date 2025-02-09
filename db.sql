-------------------------------------------------------------------------------
--------------------------------EXTENSIONS-------------------------------------
-------------------------------------------------------------------------------

CREATE EXTENSION IF NOT EXISTS ltree;
CREATE EXTENSION IF NOT EXISTS citext;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-------------------------------------------------------------------------------
-----------------------------------TABLES--------------------------------------
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
-- Facilita a busca por usernames
CREATE INDEX idx_users_username_trgm ON users USING GIN (username gin_trgm_ops);

-------------------------------------------------------------------------------
-------------------------------------------------------------------------------
CREATE TABLE images (
    image_id BIGSERIAL PRIMARY KEY NOT NULL,
    image_url TEXT NOT NULL,
    public_id TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
) PARTITION BY HASH (image_id);
CREATE TABLE images_0 PARTITION OF images FOR VALUES WITH (MODULUS 8, REMAINDER 0);
CREATE TABLE images_1 PARTITION OF images FOR VALUES WITH (MODULUS 8, REMAINDER 1);
CREATE TABLE images_2 PARTITION OF images FOR VALUES WITH (MODULUS 8, REMAINDER 2);
CREATE TABLE images_3 PARTITION OF images FOR VALUES WITH (MODULUS 8, REMAINDER 3);
CREATE TABLE images_4 PARTITION OF images FOR VALUES WITH (MODULUS 8, REMAINDER 4);
CREATE TABLE images_5 PARTITION OF images FOR VALUES WITH (MODULUS 8, REMAINDER 5);
CREATE TABLE images_6 PARTITION OF images FOR VALUES WITH (MODULUS 8, REMAINDER 6);
CREATE TABLE images_7 PARTITION OF images FOR VALUES WITH (MODULUS 8, REMAINDER 7);

-------------------------------------------------------------------------------
-------------------------------------------------------------------------------

CREATE TABLE users_profile_images (
    user_id INTEGER PRIMARY KEY NOT NULL,
    profile_image_id BIGINT DEFAULT NULL,
    cover_image_id BIGINT DEFAULT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_user_profile_photos_user_id FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_user_profile_photos_profile_image_id FOREIGN KEY (profile_image_id) REFERENCES images(image_id) ON DELETE SET DEFAULT,
    CONSTRAINT fk_user_profile_photos_cover_image_id FOREIGN KEY (cover_image_id) REFERENCES images(image_id) ON DELETE SET DEFAULT
) PARTITION BY HASH (user_id);
CREATE TABLE users_profile_images_0 PARTITION OF users_profile_images FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE users_profile_images_1 PARTITION OF users_profile_images FOR VALUES WITH (MODULUS 4, REMAINDER 1);
CREATE TABLE users_profile_images_2 PARTITION OF users_profile_images FOR VALUES WITH (MODULUS 4, REMAINDER 2);
CREATE TABLE users_profile_images_3 PARTITION OF users_profile_images FOR VALUES WITH (MODULUS 4, REMAINDER 3);

-------------------------------------------------------------------------------
-------------------------------------------------------------------------------

CREATE TABLE languages (
    code VARCHAR(5) PRIMARY KEY CHECK (code ~ '^[a-z]{2}(-[A-Z]{2})?$'),
    name VARCHAR(64) NOT NULL,
    native_name VARCHAR(64)
);

INSERT INTO  languages 
    (code, name, native_name)
VALUES    
    ('en-US', 'English', 'English'),
    ('pt-BR', 'Portuguese', 'Português');

-------------------------------------------------------------------------------
-------------------------------------------------------------------------------

CREATE TYPE 
    post_status_type
AS ENUM  (
    'draft', 
    'published',
    'archived'
);

-------------------------------------------------------------------------------
-------------------------------------------------------------------------------

CREATE TABLE posts (
    post_id SERIAL PRIMARY KEY NOT NULL,
    user_id INTEGER NOT NULL,
    title VARCHAR(256) NOT NULL,
    content TEXT,
    language VARCHAR(8),
    status post_status_type NOT NULL,
    is_pinned BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT posts_fk_user FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
    CONSTRAINT posts_fk_language FOREIGN KEY (language) REFERENCES languages (code)
);
CREATE INDEX idx_posts_user_id ON posts(user_id);
CREATE INDEX idx_posts_user_created_at ON posts (user_id, created_at DESC);
CREATE INDEX idx_posts_status_order ON posts (status, created_at DESC);
CREATE INDEX idx_posts_language ON posts(language);
CREATE INDEX idx_posts_created_at ON posts(created_at);
CREATE INDEX idx_posts_published ON posts(status) WHERE status = 'published';
CREATE INDEX idx_posts_published_created_at ON posts(created_at) WHERE status = 'published';
CREATE INDEX idx_posts_updated_at ON posts(updated_at);
CREATE INDEX idx_posts_user_status ON posts(user_id, status);
CREATE INDEX idx_posts_title_fulltext_br ON posts USING GIN (to_tsvector('portuguese', title));
CREATE INDEX idx_posts_title_fulltext_en ON posts USING GIN (to_tsvector('english', title));

-------------------------------------------------------------------------------
-------------------------------------------------------------------------------

CREATE TABLE post_images (    
    post_id INTEGER NOT NULL,
    image_id BIGINT NOT NULL,
    position INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (post_id, position),
    CONSTRAINT post_images_fk_post FOREIGN KEY (post_id) REFERENCES posts (post_id) ON DELETE CASCADE,
    CONSTRAINT post_images_fk_image FOREIGN KEY (image_id) REFERENCES images (image_id) ON DELETE CASCADE
) PARTITION BY HASH (post_id);
CREATE TABLE post_images_0 PARTITION OF post_images FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE post_images_1 PARTITION OF post_images FOR VALUES WITH (MODULUS 4, REMAINDER 1);
CREATE TABLE post_images_2 PARTITION OF post_images FOR VALUES WITH (MODULUS 4, REMAINDER 2);
CREATE TABLE post_images_3 PARTITION OF post_images FOR VALUES WITH (MODULUS 4, REMAINDER 3);

-------------------------------------------------------------------------------
-------------------------------------------------------------------------------

CREATE TABLE post_likes (
    post_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,    
    PRIMARY KEY (post_id, user_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (post_id) REFERENCES posts (post_id) ON DELETE CASCADE
) PARTITION BY HASH (post_id);
CREATE TABLE post_likes_0 PARTITION OF post_likes FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE post_likes_1 PARTITION OF post_likes FOR VALUES WITH (MODULUS 4, REMAINDER 1);
CREATE TABLE post_likes_2 PARTITION OF post_likes FOR VALUES WITH (MODULUS 4, REMAINDER 2);
CREATE TABLE post_likes_3 PARTITION OF post_likes FOR VALUES WITH (MODULUS 4, REMAINDER 3);
CREATE INDEX idx_post_likes_post ON post_likes(post_id);

-------------------------------------------------------------------------------
-------------------------------------------------------------------------------

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
CREATE INDEX idx_comments_post ON comments (post_id);
CREATE INDEX idx_comments_parent ON comments (parent_comment_id);
CREATE INDEX idx_comments_path ON comments USING GIST (path);
CREATE INDEX idx_comments_order ON comments (post_id, created_at);

-------------------------------------------------------------------------------
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
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, post_id, hashtag_id),
    CONSTRAINT post_hashtags_fk_user FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
    CONSTRAINT post_hashtags_fk_post FOREIGN KEY (post_id) REFERENCES posts (post_id) ON DELETE CASCADE,
    CONSTRAINT post_hashtags_fk_hashtag FOREIGN KEY (hashtag_id) REFERENCES hashtags (hashtag_id) ON DELETE CASCADE
) PARTITION BY HASH (post_id);
CREATE TABLE post_hashtags_0 PARTITION OF post_hashtags FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE post_hashtags_1 PARTITION OF post_hashtags FOR VALUES WITH (MODULUS 4, REMAINDER 1);
CREATE TABLE post_hashtags_2 PARTITION OF post_hashtags FOR VALUES WITH (MODULUS 4, REMAINDER 2);
CREATE TABLE post_hashtags_3 PARTITION OF post_hashtags FOR VALUES WITH (MODULUS 4, REMAINDER 3);

-------------------------------------------------------------------------------
-------------------------------------------------------------------------------

CREATE TYPE metric_type AS ENUM (
    'impressions', 
    'views'    
);

-------------------------------------------------------------------------------
-------------------------------------------------------------------------------

CREATE TABLE post_metrics (
    post_id INTEGER NOT NULL,
    counter BIGINT NOT NULL DEFAULT 0,    
    type metric_type NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (post_id, type),
    CONSTRAINT post_metrics_fk_post FOREIGN KEY (post_id) REFERENCES posts (post_id) ON DELETE CASCADE,
    CONSTRAINT post_metrics_chk_positive_counter CHECK (counter >= 0)
) PARTITION BY LIST (type);

CREATE TABLE post_metrics_impressions PARTITION OF post_metrics FOR VALUES IN ('impressions');
ALTER TABLE post_metrics_impressions SET (fillfactor = 80);
CREATE TABLE post_metrics_views PARTITION OF post_metrics FOR VALUES IN ('views');
ALTER TABLE post_metrics_views SET (fillfactor = 80);

-------------------------------------------------------------------------------
-------------------------------------------------------------------------------

CREATE TABLE comment_metrics (
    comment_id INTEGER NOT NULL,
    counter BIGINT NOT NULL DEFAULT 0,
    type metric_type NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (comment_id, type),
    CONSTRAINT comment_metrics_fk_comment FOREIGN KEY (comment_id) REFERENCES comments (comment_id) ON DELETE CASCADE,
    CONSTRAINT comment_metrics_chk_positive_counter CHECK (counter >= 0)
) PARTITION BY LIST (type);


CREATE TABLE comment_metrics_impressions PARTITION OF comment_metrics FOR VALUES IN ('impressions');
ALTER TABLE comment_metrics_impressions SET (fillfactor = 80);
CREATE TABLE comment_metrics_views PARTITION OF comment_metrics FOR VALUES IN ('views');
ALTER TABLE  comment_metrics_views  SET (fillfactor = 80);

-------------------------------------------------------------------------------
-------------------------------------------------------------------------------

CREATE TABLE direct_conversations (    
    conversation_id SERIAL PRIMARY KEY,
    user1_id INTEGER NOT NULL,
    user2_id INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_interaction_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    UNIQUE (user1_id, user2_id),
    CONSTRAINT direct_conversations_fk_user1 FOREIGN KEY (user1_id) REFERENCES users(user_id),
    CONSTRAINT direct_conversations_fk_user2 FOREIGN KEY (user2_id) REFERENCES users(user_id),
    CONSTRAINT direct_conversations_chk_user_order CHECK (user1_id < user2_id)
);
CREATE INDEX idx_direct_conversations_user1 ON direct_conversations(user1_id);
CREATE INDEX idx_direct_conversations_user2 ON direct_conversations(user2_id);

-------------------------------------------------------------------------------
-------------------------------------------------------------------------------

CREATE TABLE messages (
    message_id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL,
    sender_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN DEFAULT FALSE,
    is_edited BOOLEAN DEFAULT FALSE,
    reply_to_message_id INTEGER,
    CONSTRAINT messages_fk_conversation_id FOREIGN KEY (conversation_id) REFERENCES direct_conversations(conversation_id) ON DELETE CASCADE,
    CONSTRAINT messages_fk_sender_id FOREIGN KEY (sender_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT messages_fk_reply_to_id FOREIGN KEY (reply_to_message_id) REFERENCES messages(message_id) ON DELETE SET NULL
);
CREATE INDEX idx_messages_conversation ON messages(conversation_id, created_at DESC);
CREATE INDEX idx_messages_conversation_created ON messages(conversation_id, created_at);

-------------------------------------------------------------------------------
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
-----------------------------FUNCTIONS AND TRIGGERS----------------------------
-------------------------------------------------------------------------------

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
-------------------------------------------------------------------------------

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

-------------------------------------------------------------------------------
-------------------------------------------------------------------------------
-- Atualiza o campo path da tabela comments (hierarquia de comentários)

CREATE OR REPLACE FUNCTION update_comment_path()
RETURNS TRIGGER AS $$
BEGIN
    -- If it's a top-level comment (no parent)
    IF NEW.parent_comment_id IS NULL THEN
        NEW.path = NEW.comment_id::text::ltree;
    ELSE
        -- Get the parent's path and append the new comment's ID
        SELECT path || NEW.comment_id::text
        INTO NEW.path
        FROM comments
        WHERE comment_id = NEW.parent_comment_id;

        -- Check if parent_comment_id exists (important for data integrity, avoiding trigger failure)
        IF NOT FOUND THEN
          RAISE EXCEPTION 'Parent comment with ID % not found', NEW.parent_comment_id;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_comment_path_trigger
BEFORE INSERT ON comments
FOR EACH ROW
EXECUTE FUNCTION update_comment_path();

-------------------------------------------------------------------------------
-------------------------------------------------------------------------------
-- Retorna toda a hierarquia de comentários de um único comentário

CREATE OR REPLACE FUNCTION get_comment_children(p_parent_id INTEGER)
RETURNS JSON AS $$
DECLARE
    children JSON;
BEGIN
    SELECT COALESCE(
        json_agg(
            json_build_object(
                'comment_id', c.comment_id,
                'user_id', c.user_id,
                'content', c.content,
                'created_at', TO_CHAR(c.created_at, 'YYYY-MM-DD HH24:MI:SS'),
                'updated_at', TO_CHAR(c.updated_at, 'YYYY-MM-DD HH24:MI:SS'),
                'metrics', get_comment_metrics(c.comment_id),
                'replies', get_comment_children(c.comment_id),
                'parent_comment_id', c.parent_comment_id
            )
        ),
        '[]'::json
    )
    INTO children
    FROM comments c
    WHERE c.parent_comment_id = p_parent_id;

    RETURN children;
END;
$$ LANGUAGE plpgsql;

-------------------------------------------------------------------------------
-------------------------------------------------------------------------------
-- Retorna toda a hierarquia de comentários de uma postagem

CREATE OR REPLACE FUNCTION get_post_comments(p_post_id INTEGER)
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    SELECT COALESCE(
        json_agg(
            json_build_object(
                'comment_id', c.comment_id,
                'user_id', c.user_id,
                'content', c.content,
                'created_at', TO_CHAR(c.created_at, 'YYYY-MM-DD HH24:MI:SS'),
                'updated_at', TO_CHAR(c.updated_at, 'YYYY-MM-DD HH24:MI:SS'),
                'metrics', get_comment_metrics(c.comment_id),
                'replies', get_comment_children(c.comment_id),
                'parent_comment_id', c.parent_comment_id
            )
        ),
        '[]'::json
    )
    INTO result
    FROM comments c
    WHERE c.post_id = p_post_id
      AND c.parent_comment_id IS NULL;

    RETURN result;
END;
$$ LANGUAGE plpgsql;

-------------------------------------------------------------------------------
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
-------------------------------------------------------------------------------
-- Mantem o histórico de posts vistos por cada usuário em até 40 posts
-- Função para ser executada todos os dias as 3:00 de manhã via cron

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
-------------------------------------------------------------------------------
-- Verifica se o usuário está dando like em um comentário
--  1. Que existe
--  2. Que pertence a postagem correta

CREATE OR REPLACE FUNCTION validate_comment_likes()
RETURNS TRIGGER AS $$
DECLARE
    comment_post_id INTEGER;
BEGIN
    -- Recupera o post_id do comentário referenciado
    SELECT post_id 
      INTO comment_post_id 
      FROM comments 
     WHERE comment_id = NEW.comment_id;

    -- Verifica se o comentário existe; caso não exista, gera uma exceção
    IF NOT FOUND THEN
        RAISE EXCEPTION 'O comentário com ID % não existe.', NEW.comment_id;
    END IF;

    -- Verifica se o post_id do comentário é igual ao post_id da linha em comment_likes
    IF comment_post_id <> NEW.post_id THEN
        RAISE EXCEPTION 'O comentário com ID % não pertence ao post com ID %.', NEW.comment_id, NEW.post_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_validate_comment_likes
BEFORE INSERT OR UPDATE ON comment_likes
FOR EACH ROW
EXECUTE FUNCTION validate_comment_likes();

-------------------------------------------------------------------------------
-------------------------------------------------------------------------------
-- Verifica se o usuário que está enviando a mensagem
--  1. Está inserindo uma mensagem em uma conversa existente
--  2. Está participando da conversa
--  3. Está enviando uma mensagem para alguem que não o bloqueou
--  4. Está respondendo (caso esteja respondendo) a uma mensagem válida dentro da conversa

CREATE OR REPLACE FUNCTION validate_message()
RETURNS TRIGGER AS $$
DECLARE
    conv_record RECORD;
    recipient_id INTEGER;
    is_blocked BOOLEAN;
    reply_conv_id INTEGER;
BEGIN
    -- Recupera os dados da conversa
    SELECT user1_id, user2_id
      INTO conv_record
      FROM direct_conversations
     WHERE conversation_id = NEW.conversation_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Conversation with ID % does not exist.', NEW.conversation_id;
    END IF;

    -- Determina o destinatário (o outro participante)
    IF NEW.sender_id = conv_record.user1_id THEN
        recipient_id := conv_record.user2_id;
    ELSIF NEW.sender_id = conv_record.user2_id THEN
        recipient_id := conv_record.user1_id;
    ELSE
        RAISE EXCEPTION 'Sender ID % is not a participant in conversation %.', NEW.sender_id, NEW.conversation_id;
    END IF;

    -- Verifica se o destinatário bloqueou o remetente
    SELECT EXISTS (
        SELECT 1 
          FROM blocks 
         WHERE blocker_id = recipient_id 
           AND blocked_id = NEW.sender_id
    )
      INTO is_blocked;

    IF is_blocked THEN
        RAISE EXCEPTION 'Message cannot be created because the sender (ID: %) is blocked by the recipient (ID: %).', NEW.sender_id, recipient_id;
    END IF;
    
    -- Validação adicional: se reply_to_message_id estiver definido,
    -- verifica se a mensagem referenciada existe e pertence à mesma conversa.
    IF NEW.reply_to_message_id IS NOT NULL THEN
        SELECT conversation_id 
          INTO reply_conv_id
          FROM messages 
         WHERE message_id = NEW.reply_to_message_id;

        IF NOT FOUND THEN
            RAISE EXCEPTION 'Referenced reply message with ID % does not exist.', NEW.reply_to_message_id;
        END IF;

        IF reply_conv_id <> NEW.conversation_id THEN
            RAISE EXCEPTION 'Reply message (ID: %) does not belong to conversation %.', NEW.reply_to_message_id, NEW.conversation_id;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_validate_message
BEFORE INSERT ON messages
FOR EACH ROW
EXECUTE FUNCTION validate_message();

-------------------------------------------------------------------------------
-------------------------------------------------------------------------------
-- Não permite que um usuário siga alguem caso esteja bloqueado

CREATE OR REPLACE FUNCTION validate_follow_block()
RETURNS TRIGGER AS $$
DECLARE
    is_blocked BOOLEAN;
BEGIN
    -- Verifica se existe um registro na tabela blocks em que o followed_id bloqueou o follower_id
    SELECT EXISTS (
        SELECT 1 
        FROM blocks 
        WHERE blocker_id = NEW.followed_id
          AND blocked_id = NEW.follower_id
    )
    INTO is_blocked;
    
    IF is_blocked THEN
        RAISE EXCEPTION 'A conta com ID % bloqueou o usuário com ID %. A operação de seguir não pode ser realizada.', NEW.followed_id, NEW.follower_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_validate_follow_block
BEFORE INSERT OR UPDATE ON follows
FOR EACH ROW
EXECUTE FUNCTION validate_follow_block();

-------------------------------------------------------------------------------
-------------------------------------------------------------------------------
-- Caso usuário A de block em um usuário B, os follows de A para B e da B para A são deletados

CREATE OR REPLACE FUNCTION unfollow_on_block()
RETURNS TRIGGER AS $$
BEGIN
    -- Remove quaisquer relações de follow existentes entre o blocker e o blocked
    DELETE FROM follows
    WHERE (follower_id = NEW.blocker_id AND followed_id = NEW.blocked_id)
       OR (follower_id = NEW.blocked_id AND followed_id = NEW.blocker_id);
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_unfollow_on_block
AFTER INSERT ON blocks
FOR EACH ROW
EXECUTE FUNCTION unfollow_on_block();
