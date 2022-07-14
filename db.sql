CREATE DATABASE blog;

CREATE TABLE posts (
    post_id VARCHAR(10),
    post_dt VARCHAR(15),
    image_path VARCHAR(50),
    title VARCHAR(50),
    content VARCHAR(2000)
);

CREATE TABLE comments (
    post_id VARCHAR(10),
    dt VARCHAR(15),
    name VARCHAR(15),
    comment VARCHAR(250)
);
