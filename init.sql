-- init.sql
CREATE DATABASE mydatabase;
CREATE USER myuser WITH ENCRYPTED PASSWORD 'mypassword';
GRANT ALL PRIVILEGES ON DATABASE mydatabase TO myuser;


-- Switch to the newly created database
\c mydatabase;

-- Initialize Seller table
CREATE TABLE IF NOT EXISTS Seller (
    seller_id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    rating FLOAT,
    reviews INT,
    subscribers INT,
    subscriptions INT,
    registered VARCHAR(255),
    done_deals INT,
    active_deals INT,
    docs_confirmed BOOLEAN,
    phone_confirmed BOOLEAN,
    response_time VARCHAR(255)
);

-- Initialize Product table
CREATE TABLE IF NOT EXISTS Product (
    link VARCHAR(255) PRIMARY KEY,
    version INT,
    condition VARCHAR(255),
    is_pro BOOLEAN,
    is_max BOOLEAN,
    capacity INT,
    price_coeff FLOAT,
    title VARCHAR(255) NOT NULL,
    price FLOAT NOT NULL,
    characteristics TEXT,
    description TEXT,
    views INT,
    date VARCHAR(255),
    location VARCHAR(255),
    seller_id VARCHAR(255) NOT NULL,
    today_views INT,
    about TEXT,
    is_sold BOOLEAN NOT NULL
);

-- Initialize Telegram subscribers table
CREATE TABLE Subscribers (
    chat_id BIGINT PRIMARY KEY,
    subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE Seller TO myuser;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE Product TO myuser;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE Subscribers TO myuser;
