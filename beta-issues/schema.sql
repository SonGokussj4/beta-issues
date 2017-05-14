DROP TABLE if exists entries;
CREATE TABLE entries (
    id INTEGER PRIMARY KEY autoincrement,
    title TEXT NOT NULL,
    'text' TEXT NOT NULL
);

DROP TABLE if exists issues;
CREATE TABLE issues (
    id INTEGER PRIMARY KEY autoincrement,
    title TEXT NOT NULL,
    priority INTEGER NOT NULL,
    'datum' text NOT NULL,
    'description' TEXT NOT NULL,
    'comment' TEXT NOT NULL
);