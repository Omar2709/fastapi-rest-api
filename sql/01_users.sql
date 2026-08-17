CREATE TABLE users (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    name VARCHAR(50)
        NOT NULL
        CHECK (char_length(trim(name)) >= 2),

    email VARCHAR(255)
        NOT NULL
        UNIQUE,

    created_at TIMESTAMPTZ
        NOT NULL
        DEFAULT CURRENT_TIMESTAMP
);


INSERT INTO users (name, email)
VALUES
    ('Ana', 'ana@example.com'),
    ('Carlos', 'carlos@example.com');


SELECT id, name, email, created_at
FROM users;

