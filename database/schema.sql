-- ====================================================================
-- AI SHOPPING ASSISTANT - DATABASE SCHEMA (MySQL 8.0+)
-- Synchronized with SQLAlchemy ORM Models
-- ====================================================================

CREATE DATABASE IF NOT EXISTS `ai_shopping_assistant` 
DEFAULT CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE `ai_shopping_assistant`;

-- Drop existing tables in reverse dependency order
DROP TABLE IF EXISTS `shopping_planner`;
DROP TABLE IF EXISTS `recommendations`;
DROP TABLE IF EXISTS `chat_history`;
DROP TABLE IF EXISTS `cart`;
DROP TABLE IF EXISTS `login_history`;
DROP TABLE IF EXISTS `products`;
DROP TABLE IF EXISTS `categories`;
DROP TABLE IF EXISTS `users`;

-- --------------------------------------------------------------------
-- 1. USERS TABLE
-- --------------------------------------------------------------------
CREATE TABLE `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(80) NOT NULL UNIQUE,
    `email` VARCHAR(120) NOT NULL UNIQUE,
    `password_hash` VARCHAR(255) NOT NULL,
    `first_name` VARCHAR(50) DEFAULT NULL,
    `last_name` VARCHAR(50) DEFAULT NULL,
    `role` ENUM('user', 'admin') DEFAULT 'user' NOT NULL,
    `is_active` TINYINT(1) DEFAULT 1 NOT NULL,
    `email_verified` TINYINT(1) DEFAULT 1 NOT NULL,
    `verification_otp` VARCHAR(6) DEFAULT NULL,
    `verification_otp_expiry` DATETIME DEFAULT NULL,
    `reset_otp` VARCHAR(6) DEFAULT NULL,
    `reset_otp_expiry` DATETIME DEFAULT NULL,
    `login_token` VARCHAR(100) DEFAULT NULL,
    `login_token_expiry` DATETIME DEFAULT NULL,
    `pending_ip` VARCHAR(45) DEFAULT NULL,
    `pending_browser` VARCHAR(100) DEFAULT NULL,
    `pending_os` VARCHAR(100) DEFAULT NULL,
    `pending_device` VARCHAR(100) DEFAULT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL,
    INDEX `idx_users_username` (`username`),
    INDEX `idx_users_email` (`email`),
    INDEX `idx_users_login_token` (`login_token`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------------------
-- 2. CATEGORIES TABLE
-- --------------------------------------------------------------------
CREATE TABLE `categories` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) NOT NULL UNIQUE,
    `slug` VARCHAR(100) NOT NULL UNIQUE,
    `description` TEXT DEFAULT NULL,
    `is_active` TINYINT(1) DEFAULT 1 NOT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    INDEX `idx_categories_name` (`name`),
    INDEX `idx_categories_slug` (`slug`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------------------
-- 3. PRODUCTS TABLE
-- --------------------------------------------------------------------
CREATE TABLE `products` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `sku` VARCHAR(50) NOT NULL UNIQUE,
    `slug` VARCHAR(255) NOT NULL UNIQUE,
    `name` VARCHAR(255) NOT NULL,
    `brand` VARCHAR(100) NOT NULL,
    `category_id` INT NOT NULL,
    `price` DECIMAL(10, 2) NOT NULL,
    `rating` DECIMAL(3, 2) DEFAULT 0.00 NOT NULL,
    `description` TEXT DEFAULT NULL,
    `specifications` JSON DEFAULT NULL,
    `image_url` VARCHAR(500) DEFAULT NULL,
    `stock_quantity` INT DEFAULT 0 NOT NULL,
    `is_available` TINYINT(1) DEFAULT 1 NOT NULL,
    `is_active` TINYINT(1) DEFAULT 1 NOT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (`category_id`) REFERENCES `categories` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
    INDEX `idx_products_sku` (`sku`),
    INDEX `idx_products_slug` (`slug`),
    INDEX `idx_products_name` (`name`),
    INDEX `idx_products_brand` (`brand`),
    INDEX `idx_products_category` (`category_id`),
    INDEX `idx_product_brand_category` (`brand`, `category_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------------------
-- 4. LOGIN HISTORY TABLE
-- --------------------------------------------------------------------
CREATE TABLE `login_history` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `login_time` DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    `ip_address` VARCHAR(45) DEFAULT NULL,
    `browser` VARCHAR(100) DEFAULT NULL,
    `operating_system` VARCHAR(100) DEFAULT NULL,
    `device_name` VARCHAR(100) DEFAULT NULL,
    `status` ENUM('APPROVED', 'DENIED', 'EXPIRED') DEFAULT 'APPROVED' NOT NULL,
    FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX `idx_login_history_user` (`user_id`),
    INDEX `idx_login_history_time` (`login_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------------------
-- 5. CART TABLE
-- --------------------------------------------------------------------
CREATE TABLE `cart` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `product_id` INT NOT NULL,
    `quantity` INT DEFAULT 1 NOT NULL,
    `added_at` DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    UNIQUE KEY `uq_user_product_cart` (`user_id`, `product_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------------------
-- 6. CHAT HISTORY TABLE
-- --------------------------------------------------------------------
CREATE TABLE `chat_history` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `user_message` TEXT NOT NULL,
    `ai_response` TEXT NOT NULL,
    `intent` VARCHAR(100) DEFAULT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX `idx_chat_user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------------------
-- 7. RECOMMENDATIONS TABLE
-- --------------------------------------------------------------------
CREATE TABLE `recommendations` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `product_id` INT NOT NULL,
    `recommendation_score` DECIMAL(5, 2) DEFAULT 0.00 NOT NULL,
    `reason` VARCHAR(255) DEFAULT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX `idx_recommendations_user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------------------
-- 8. SHOPPING PLANNER TABLE
-- --------------------------------------------------------------------
CREATE TABLE `shopping_planner` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `plan_name` VARCHAR(150) NOT NULL,
    `budget` DECIMAL(10, 2) NOT NULL,
    `target_date` DATE DEFAULT NULL,
    `selected_items` JSON DEFAULT NULL,
    `status` ENUM('draft', 'active', 'completed') DEFAULT 'draft' NOT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX `idx_planner_user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
