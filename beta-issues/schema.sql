DROP TABLE if exists users;
CREATE TABLE users (
    id INTEGER PRIMARY KEY autoincrement,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    email TEXT NOT NULL,
    settings TEXT
);

DROP TABLE if exists issues;
CREATE TABLE issues (
    id INTEGER PRIMARY KEY autoincrement,
    issue TEXT NOT NULL,
    description TEXT NOT NULL,
    date_issued TEXT NOT NULL,
    author TEXT,
    details TEXT,
    date_resolved TEXT,
    version TEXT
);

DROP TABLE if exists resolved_issues;
CREATE TABLE resolved_issues (
    id INTEGER PRIMARY KEY autoincrement,
    issue TEXT NOT NULL,
    version TEXT,
    date_resolved TEXT
);

