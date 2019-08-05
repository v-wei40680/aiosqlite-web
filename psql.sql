create table if not exists users (
id varchar(50) not null primary key,
email varchar(50) not null unique,
passwd varchar(50) not null,
admin bool not null,
name varchar(50) not null,
image varchar(500) not null,
created_at float8 not null
);

# CREATE INDEX created_at_idx ON users (created_at);

-- psql.sql
create table if not exists blogs (
id varchar(50) not null primary key,
user_id varchar(50) not null,
user_name varchar(50) not null,
user_image varchar(500) not null,
name varchar(50) not null,
summary varchar(200) not null,
content text not null,
created_at float8 not null,
readable bool not null,
read_count int not null
);

create table if not exists comments (
id varchar(50) not null primary key,
blog_id varchar(50) not null,
user_id varchar(50) not null,
user_name varchar(50) not null,
user_image varchar(500) not null,
content text not null,
created_at float8 not null
);

create table if not exists flags (
id varchar(50) not null primary key,
nick varchar(50) not null,
tradeId varchar(50) not null,
created_at float8 not null,
createTime varchar(50) not null,
flag int not null,
shop varchar(50) not null,
status varchar(50) not null
);

create table if not exists cookies (
id varchar(50) not null primary key,
cookie_str varchar(50) not null
);