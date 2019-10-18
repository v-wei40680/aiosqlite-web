create table if not exists trades (
id varchar(50) not null primary key,
nick varchar(50) not null,
created_at float8 not null,
createTime varchar(50) not null,
flag varchar(50) not null,
price varchar(50) not null,
shop varchar(50) not null,
status varchar(50) not null,
wuliu varchar(50)
);

create table if not exists fapiaos (
id varchar(50) not null primary key,
nick varchar(50) not null,
created_at float8 not null,
createTime varchar(50) not null,
flag varchar(50) not null,
price varchar(50) not null,
shop varchar(50) not null,
status varchar(50) not null,
mark text not null,
msg text not null
);

create table if not exists cookies (
id varchar(50) not null primary key,
created_at float8 not null,
updated_at float8,
cookie_str varchar(50) not null
);

create table if not exists todos (
id varchar(50) not null primary key,
itemId varchar(50),
task varchar(500) not null,
kw varchar(50),
created_at float8 not null,
updated_at float8
);