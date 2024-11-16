CREATE TABLE IF NOT EXISTS urls(
    id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name VARCHAR(255) NOT NULL,
    created_at timestamp NOT NULL
);

CREATE TABLE IF NOT EXISTS url_checks (
    id bigint PRIMARY KEY  GENERATED ALWAYS AS IDENTITY,
    url_id bigint REFERENCES urls (id),
    status_code int NOT NULL,
    h1 varchar(255),
    title varchar(255),
    description text,
    created_at timestamp NOT NULL
);