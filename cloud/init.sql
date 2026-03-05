-- Maak een tabel users aan
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL
);

-- Voeg alvast één initiële rij toe
INSERT INTO users (name, email)
VALUES ('Initial User', 'initial@example.com');