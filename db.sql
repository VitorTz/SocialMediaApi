CREATE EXTENSION IF NOT EXISTS ltree;
CREATE EXTENSION IF NOT EXISTS citext;


CREATE TABLE users (
    id SERIAL PRIMARY KEY,    
    username CITEXT UNIQUE NOT NULL,
    email CITEXT UNIQUE NOT NULL,
    full_name VARCHAR (64) NOT NULL,
    hashed_password VARCHAR(256) NOT NULL,
    bio TEXT,
    birthdate DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_verified BOOLEAN NOT NULL DEFAULT false,
    CONSTRAINT chk_user_age CHECK (birthdate <= CURRENT_DATE - INTERVAL '16 years'),
    CONSTRAINT chk_user_username_length CHECK (LENGTH(username) <= 32),
    CONSTRAINT chk_user_email_length CHECK (LENGTH(email) <= 255),
    CONSTRAINT chk_user_email_format CHECK (email ~* '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
);


CREATE TABLE languages (
    code VARCHAR(8) PRIMARY KEY CHECK (code ~ '^[a-z]{2}(-[A-Z]{2})?$'),
    name VARCHAR(64) NOT NULL, -- Ex: 'Português'
    native_name VARCHAR(64) -- Ex: 'Português Brasileiro'
);


CREATE TABLE post_status (
    status VARCHAR(32) PRIMARY KEY
); -- ('draft', 'published')


CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    title VARCHAR(256) NOT NULL,
    content TEXT,
    is_pinned BOOLEAN NOT NULL DEFAULT false,
    view_count INTEGER DEFAULT 0,
    language_code VARCHAR(8),
    status VARCHAR(32),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT fk_status FOREIGN KEY (status) REFERENCES post_status (status) ON DELETE CASCADE,
    CONSTRAINT fk_language_code FOREIGN KEY (language_code) REFERENCES languages (code) ON DELETE CASCADE
);
CREATE INDEX idx_posts_user_id ON posts(user_id);
CREATE INDEX idx_posts_language ON posts(language_code);
CREATE INDEX idx_posts_created_at ON posts(created_at);


-- Tabela para guardar histórico de post vistos por um usuário
CREATE TABLE user_viewed_posts (
    user_id INTEGER NOT NULL,
    post_id INTEGER NOT NULL,
    viewed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, post_id)
) PARTITION BY HASH (user_id);
-- Partições e indices de user_viewed_posts
CREATE TABLE user_viewed_posts_0 PARTITION OF user_viewed_posts FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE user_viewed_posts_1 PARTITION OF user_viewed_posts FOR VALUES WITH (MODULUS 4, REMAINDER 1);
CREATE TABLE user_viewed_posts_2 PARTITION OF user_viewed_posts FOR VALUES WITH (MODULUS 4, REMAINDER 2);
CREATE TABLE user_viewed_posts_3 PARTITION OF user_viewed_posts FOR VALUES WITH (MODULUS 4, REMAINDER 3);
CREATE INDEX idx_user_viewed_posts_0 ON user_viewed_posts_0(user_id, viewed_at DESC);
CREATE INDEX idx_user_viewed_posts_1 ON user_viewed_posts_1(user_id, viewed_at DESC);
CREATE INDEX idx_user_viewed_posts_2 ON user_viewed_posts_2(user_id, viewed_at DESC);
CREATE INDEX idx_user_viewed_posts_3 ON user_viewed_posts_3(user_id, viewed_at DESC);


-- Tabelas para hashtags
CREATE TABLE hashtags (
    id SERIAL PRIMARY KEY,
    name CITEXT UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE post_hashtags (
    post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    hashtag_id INTEGER NOT NULL REFERENCES hashtags(id) ON DELETE CASCADE,
    PRIMARY KEY (post_id, hashtag_id)
);


CREATE TABLE comments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    post_id INTEGER NOT NULL,
    content TEXT,
    parent_comment_id INTEGER,
    path LTREE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_post FOREIGN KEY (post_id) REFERENCES posts (id) ON DELETE CASCADE,
    CONSTRAINT fk_parent FOREIGN KEY (parent_comment_id) REFERENCES comments (id) ON DELETE CASCADE
);
CREATE INDEX idx_comments_post_id ON comments(post_id);
CREATE INDEX idx_comments_parent ON comments(parent_comment_id);
CREATE INDEX idx_comments_path ON comments USING GIST (path);
CREATE INDEX idx_comments_user_created ON comments(user_id, created_at);


-- Tabela para conversar privadas entre usuários
CREATE TABLE direct_conversations (
    id SERIAL PRIMARY KEY,
    user1_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    user2_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,    
    CHECK (user1_id < user2_id),    
    UNIQUE (user1_id, user2_id)
);
CREATE INDEX idx_direct_conversations_user1 ON direct_conversations(user1_id);
CREATE INDEX idx_direct_conversations_user2 ON direct_conversations(user2_id);


-- Tabela para mensagens contidas em uma conversa privada entre usuários
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES direct_conversations(id) ON DELETE CASCADE,
    sender_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reply_to_id INTEGER REFERENCES messages(id) ON DELETE SET NULL
);
CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_created ON messages(created_at);

-- Tabela para mensagens lidas em conversas privadas entre usuários
CREATE TABLE message_reads (
    message_id INTEGER NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    read_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (message_id, user_id)
);


-- Tabela para like em posts
CREATE TABLE post_likes (
    user_id INTEGER NOT NULL,
    post_id INTEGER NOT NULL,    
    PRIMARY KEY (user_id, post_id)
) PARTITION BY HASH (post_id);
-- Partições(4) e indices
CREATE TABLE post_likes_0 PARTITION OF post_likes FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE post_likes_1 PARTITION OF post_likes FOR VALUES WITH (MODULUS 4, REMAINDER 1);
CREATE TABLE post_likes_2 PARTITION OF post_likes FOR VALUES WITH (MODULUS 4, REMAINDER 2);
CREATE TABLE post_likes_3 PARTITION OF post_likes FOR VALUES WITH (MODULUS 4, REMAINDER 3);
CREATE INDEX ON post_likes_0 (post_id);
CREATE INDEX ON post_likes_1 (post_id);
CREATE INDEX ON post_likes_2 (post_id);
CREATE INDEX ON post_likes_3 (post_id);


-- Tabela para like em comentários
CREATE TABLE comment_likes (
    user_id INTEGER NOT NULL,
    comment_id INTEGER NOT NULL,
    PRIMARY KEY (user_id, comment_id)
) PARTITION BY HASH (comment_id);
-- Partições(4) e indices
CREATE TABLE comment_likes_0 PARTITION OF comment_likes FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE comment_likes_1 PARTITION OF comment_likes FOR VALUES WITH (MODULUS 4, REMAINDER 1);
CREATE TABLE comment_likes_2 PARTITION OF comment_likes FOR VALUES WITH (MODULUS 4, REMAINDER 2);
CREATE TABLE comment_likes_3 PARTITION OF comment_likes FOR VALUES WITH (MODULUS 4, REMAINDER 3);
CREATE INDEX ON comment_likes_0 (comment_id);
CREATE INDEX ON comment_likes_1 (comment_id);
CREATE INDEX ON comment_likes_2 (comment_id);
CREATE INDEX ON comment_likes_3 (comment_id);


-- Tabela de usuários bloqueados
CREATE TABLE blocks (
    blocker_id INTEGER NOT NULL,
    blocked_id INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_block_self CHECK (blocker_id != blocked_id),
    PRIMARY KEY (blocker_id, blocked_id)
) PARTITION BY HASH (blocker_id);
-- Partições (4 tabelas)
CREATE TABLE blocks_0 PARTITION OF blocks FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE blocks_1 PARTITION OF blocks FOR VALUES WITH (MODULUS 4, REMAINDER 1);
CREATE TABLE blocks_2 PARTITION OF blocks FOR VALUES WITH (MODULUS 4, REMAINDER 2);
CREATE TABLE blocks_3 PARTITION OF blocks FOR VALUES WITH (MODULUS 4, REMAINDER 3);
CREATE INDEX ON blocks_0 (blocker_id);
CREATE INDEX ON blocks_1 (blocker_id);
CREATE INDEX ON blocks_2 (blocker_id);
CREATE INDEX ON blocks_3 (blocker_id);


-- Tabela para follows
CREATE TABLE follows (
    follower_id INTEGER NOT NULL, -- usuario que esta seguindo
    followed_id INTEGER NOT NULL, -- usuario que esta sendo seguido
    PRIMARY KEY (follower_id, followed_id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_not_self_follow CHECK (follower_id != followed_id),
    CONSTRAINT fk_follower FOREIGN KEY (follower_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT fk_followed FOREIGN KEY (followed_id) REFERENCES users (id) ON DELETE CASCADE
) PARTITION BY HASH (follower_id);
-- Partições (4 tabelas)
CREATE TABLE follows_0 PARTITION OF follows FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE follows_1 PARTITION OF follows FOR VALUES WITH (MODULUS 4, REMAINDER 1);
CREATE TABLE follows_2 PARTITION OF follows FOR VALUES WITH (MODULUS 4, REMAINDER 2);
CREATE TABLE follows_3 PARTITION OF follows FOR VALUES WITH (MODULUS 4, REMAINDER 3);
CREATE INDEX ON follows_0 (follower_id);
CREATE INDEX ON follows_1 (follower_id);
CREATE INDEX ON follows_2 (follower_id);
CREATE INDEX ON follows_3 (follower_id);


-- INSERTIONS

INSERT INTO languages (code, name, native_name)
VALUES
    ('zh', 'Chinese', '中文'),
    ('es', 'Spanish', 'Español'),
    ('en', 'English', 'English'),
    ('hi', 'Hindi', 'हिन्दी'),
    ('ar', 'Arabic', 'العربية'),
    ('bn', 'Bengali', 'বাংলা'),
    ('pt', 'Portuguese', 'Português'),    
    ('ja', 'Japanese', '日本語');


INSERT INTO post_status (status) 
VALUES
    ('draft'), 
    ('published');

-- FUNCTIONS AND TRIGGERS

-- Função para definir automaticamente o campo 'path' de um comentário
CREATE OR REPLACE FUNCTION set_comment_path()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.parent_comment_id IS NULL THEN
        -- Caso seja um comentário raiz -> definir 'path' como o próprio ID
        NEW.path := NEW.id::TEXT::LTREE;
    ELSE
        -- Caso seja um comentário filho -> concatenar caminho do pai com o ID atual
        NEW.path := (SELECT path FROM comments WHERE id = NEW.parent_comment_id) || NEW.id::TEXT;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para chamar a função set_comment_path ao inserir um novo comentário
CREATE TRIGGER trigger_set_comment_path
BEFORE INSERT ON comments
FOR EACH ROW
EXECUTE FUNCTION set_comment_path();



-- Função para retornar um comentário e todos seus comentários filhos diretos ou indiretos
CREATE OR REPLACE FUNCTION get_comment_thread(parent_id INT)
RETURNS JSONB
LANGUAGE plpgsql STABLE AS $$
DECLARE
    parent_path LTREE;
    result JSONB;
BEGIN

    SELECT path INTO parent_path FROM comments WHERE id = parent_id;
    IF parent_path IS NULL THEN
        RETURN NULL;
    END IF;
    
    WITH RECURSIVE comment_tree AS (
        SELECT 
            c.id,
            c.content,
            c.user_id,
            c.post_id,
            c.parent_comment_id,
            c.created_at,
            c.updated_at,
            c.path,
            jsonb_build_object(
                'id', c.id,
                'content', c.content,
                'user_id', c.user_id,
                'post_id', c.post_id,
                'parent_comment_id', c.parent_comment_id,
                'created_at', TO_CHAR(c.created_at, 'DD-MM-YYYY HH24:MI:SS'),
                'updated_at', TO_CHAR(c.updated_at, 'DD-MM-YYYY HH24:MI:SS'),
                'thread', '[]'::JSONB
            ) AS thread
        FROM comments c
        WHERE c.path = parent_path  -- Comentário raiz

        UNION ALL

        SELECT 
            c.id,
            c.content,
            c.user_id,
            c.post_id,
            c.parent_comment_id,
            c.created_at,
            c.updated_at,
            c.path,
            jsonb_build_object(
                'id', c.id,
                'content', c.content,
                'user_id', c.user_id,
                'post_id', c.post_id,
                'parent_comment_id', c.parent_comment_id,
                'created_at', TO_CHAR(c.created_at, 'DD-MM-YYYY HH24:MI:SS'),
                'updated_at', TO_CHAR(c.updated_at, 'DD-MM-YYYY HH24:MI:SS'),
                'thread', '[]'::JSONB
            )
        FROM comments c
        JOIN comment_tree ct ON c.parent_comment_id = ct.id
    )
    
    SELECT jsonb_agg(thread) INTO result
    FROM comment_tree
    WHERE path = parent_path;

    RETURN result;
END;
$$;


-- Função para retornar todos os comentários relacionados a certo post
CREATE OR REPLACE FUNCTION get_post_comments(target_post_id INT)
RETURNS JSONB
LANGUAGE plpgsql STABLE AS $$
DECLARE
    result JSONB;
BEGIN
    WITH RECURSIVE comment_tree AS (
        -- Comentários raiz
        SELECT 
            c.id,
            c.content,
            c.user_id,
            c.post_id,
            c.parent_comment_id,
            c.created_at,
            c.updated_at,
            c.path,
            jsonb_build_object(
                'id', c.id,
                'content', c.content,
                'user_id', c.user_id,
                'post_id', c.post_id,
                'parent_comment_id', c.parent_comment_id,
                'created_at', TO_CHAR(c.created_at, 'DD-MM-YYYY HH24:MI:SS'),
                'updated_at', TO_CHAR(c.updated_at, 'DD-MM-YYYY HH24:MI:SS'),
                'thread', '[]'::JSONB
            ) AS thread
        FROM comments c
        WHERE 
            c.post_id = target_post_id 
            AND c.parent_comment_id IS NULL  -- Filtra apenas comentários raiz

        UNION ALL

        -- Comentários filhos
        SELECT 
            c.id,
            c.content,
            c.user_id,
            c.post_id,
            c.parent_comment_id,
            c.created_at,
            c.updated_at,
            c.path,
            jsonb_build_object(
                'id', c.id,
                'content', c.content,
                'user_id', c.user_id,
                'post_id', c.post_id,
                'parent_comment_id', c.parent_comment_id,
                'created_at', TO_CHAR(c.created_at, 'DD-MM-YYYY HH24:MI:SS'),
                'updated_at', TO_CHAR(c.updated_at, 'DD-MM-YYYY HH24:MI:SS'),
                'thread', '[]'::JSONB
            )
        FROM comments c
        JOIN comment_tree ct ON c.parent_comment_id = ct.id
    )

    SELECT jsonb_agg(thread) INTO result
    FROM comment_tree
    WHERE parent_comment_id IS NULL;

    RETURN result;
END;
$$;


-- Garante que o comentário filho pertence ao mesmo post que o comentário pai
CREATE OR REPLACE FUNCTION ensure_same_post() RETURNS TRIGGER AS $$
BEGIN    
    IF (SELECT post_id FROM comments WHERE id = NEW.parent_comment_id) <> NEW.post_id THEN
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


-- Bloqueia atualizações de post_id e parent_comment_id em comentários
CREATE OR REPLACE FUNCTION prevent_comment_fk_updates()
RETURNS TRIGGER AS $$
BEGIN
    -- Bloqueia atualização de post_id
    IF NEW.post_id IS DISTINCT FROM OLD.post_id THEN
        RAISE EXCEPTION 'Não é permitido alterar post_id de um comentário.';
    END IF;

    -- Bloqueia atualização de parent_comment_id
    IF NEW.parent_comment_id IS DISTINCT FROM OLD.parent_comment_id THEN
        RAISE EXCEPTION 'Não é permitido alterar parent_comment_id de um comentário.';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para chamar a função prevent_comment_fk_updates ao atualizar um comentário
CREATE TRIGGER trig_prevent_comment_fk_updates
BEFORE UPDATE ON comments
FOR EACH ROW
EXECUTE FUNCTION prevent_comment_fk_updates();


-- Função para atualizar a coluna updated_at sempre que uma atualização for feita
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- Trigger para set_update_at para as tabelas users, posts e comments
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


-- Função para atualizar a coluna updated_at da tabela direct_conversations
-- O valor updated_at da tabela direct_conversations representa a hora que
-- a ultima mensagem foi enviada por algum usuário na conversa
CREATE OR REPLACE FUNCTION update_conversation_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE direct_conversations 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.conversation_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
-- Trigger para update_conversation_timestamp
CREATE TRIGGER trg_update_conversation
AFTER UPDATE ON messages
FOR EACH ROW EXECUTE FUNCTION update_conversation_timestamp();


-- Caso um usuário A de block no usuário B, o usuário A para de
-- seguir automaticamente o usuário B
CREATE OR REPLACE FUNCTION delete_relationships_on_block()
RETURNS TRIGGER AS $$
BEGIN
    DELETE FROM follows 
    WHERE (follower_id = NEW.blocker_id AND followed_id = NEW.blocked_id)
       OR (follower_id = NEW.blocked_id AND followed_id = NEW.blocker_id);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
-- Trigger para delete_relationships_on_block
CREATE TRIGGER trg_delete_relationships
AFTER INSERT ON blocks
FOR EACH ROW EXECUTE FUNCTION delete_relationships_on_block();


-- Função para limitar o histórico de posts vistos recentimente
-- por um usuário em 20 posts
CREATE OR REPLACE FUNCTION limit_recent_viewed_posts()
RETURNS TRIGGER AS $$
BEGIN
    -- Exclui registros antigos além do 20º mais recente para o usuário
    DELETE FROM user_viewed_posts
    WHERE (user_id, viewed_at) IN (
        SELECT user_id, viewed_at
        FROM user_viewed_posts
        WHERE user_id = NEW.user_id
        ORDER BY viewed_at DESC
        OFFSET 20  -- Mantém apenas os 20 primeiros
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para limit_recent_viewed_posts
CREATE TRIGGER trg_limit_recent_posts
AFTER INSERT OR UPDATE ON user_viewed_posts
FOR EACH ROW EXECUTE FUNCTION limit_recent_viewed_posts();