CREATE TABLE "users" (
	"userid"	INTEGER UNIQUE,
	"username"	TEXT NOT NULL UNIQUE,
	"password"	TEXT NOT NULL,
	"apikey"	TEXT UNIQUE,
	"days"	TEXT NOT NULL,
	"times"	TEXT NOT NULL,
	"email"	TEXT,
	"locations"	TEXT NOT NULL,
	"ntfy"	TEXT,
	"config"	TEXT NOT NULL,
	PRIMARY KEY("userid" AUTOINCREMENT)
);