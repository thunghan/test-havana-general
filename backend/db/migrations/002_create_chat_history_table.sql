CREATE TABLE IF NOT EXISTS chat_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    chat_id INT NOT NULL,
    role ENUM('ai', 'human', 'human_operator') NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL DEFAULT NULL,
    FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE
);

