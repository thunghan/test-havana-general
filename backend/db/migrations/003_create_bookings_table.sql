CREATE TABLE IF NOT EXISTS bookings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    time VARCHAR(4) NOT NULL,
    chat_id INT NULL DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL DEFAULT NULL,
    FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE SET NULL,
    UNIQUE KEY unique_booking_slot (date, time, deleted_at)
);

