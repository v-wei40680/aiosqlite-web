create table if not exists users (
id varchar(50) not null primary key,
email varchar(50) not null unique,
passwd varchar(50) not null,
admin bool not null,
name varchar(50) not null,
image varchar(500) not null,
created_at float8 not null
);

CREATE INDEX created_at_idx ON users (created_at);

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

create table if not exists messages (
id varchar(50) not null primary key,
user_id varchar(50) not null,
user_name varchar(50) not null,
user_image varchar(500) not null,
to_user varchar(50) not null,
name varchar(50) not null,
summary varchar(200) not null,
content text not null,
created_at float8 not null
);

create table if not exists fos (
id varchar(50) not null primary key,
user_name varchar(50) not null,
created_at float8 not null
);

create table if not exists brothers (
id varchar(50) not null primary key,
user_id varchar(50) not null,
user_name varchar(50) not null,
shop varchar(50) not null,
do_time float8 not null,
ww_name varchar(50) not null,
price float8 not null,
commission float8 not null,
created_at float8 not null
);

create table if not exists replenishments (
id varchar(50) not null primary key,
user_name varchar(50) not null,
ww_name varchar(50) not null,
order_id varchar(50) not null,
code varchar(50) not null,
num int not null,
reason varchar(200) not null,
detail varchar(200) not null,
created_at float8 not null,
done bool not null
);
