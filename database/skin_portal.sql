-- AI Skin Health Screening Portal Database Schema

CREATE DATABASE IF NOT EXISTS `skin_portal`;
USE `skin_portal`;

-- 1. Users Table
CREATE TABLE IF NOT EXISTS `users` (
  `user_id` INT AUTO_INCREMENT PRIMARY KEY,
  `full_name` VARCHAR(100) NOT NULL,
  `email` VARCHAR(100) NOT NULL UNIQUE,
  `phone` VARCHAR(20) DEFAULT NULL,
  `password` VARCHAR(255) NOT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. Admin Table
CREATE TABLE IF NOT EXISTS `admin` (
  `admin_id` INT AUTO_INCREMENT PRIMARY KEY,
  `username` VARCHAR(50) NOT NULL UNIQUE,
  `password` VARCHAR(255) NOT NULL
);

-- 3. Screenings Table
CREATE TABLE IF NOT EXISTS `screenings` (
  `screening_id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL,
  `image_path` VARCHAR(255) NOT NULL,
  `prediction` VARCHAR(100) NOT NULL,
  `confidence` DECIMAL(5, 2) NOT NULL,
  `risk_level` VARCHAR(20) DEFAULT 'Low',
  `recommendation` TEXT NOT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`user_id`) REFERENCES `users`(`user_id`) ON DELETE CASCADE
);

-- 4. Diseases Information Table
CREATE TABLE IF NOT EXISTS `diseases` (
  `disease_id` INT AUTO_INCREMENT PRIMARY KEY,
  `disease_name` VARCHAR(100) NOT NULL UNIQUE,
  `description` TEXT NOT NULL,
  `symptoms` TEXT NOT NULL,
  `prevention` TEXT NOT NULL,
  `treatment` TEXT NOT NULL,
  `risk_level` VARCHAR(20) DEFAULT 'Moderate'
);

-- Seed Default Admin (Username: admin | Password: bcrypt of admin123 -> $2a$10$3p45W8rP.hI7/J40xO1eNu2S6V62p5s5M3uK6uL.5m44hGf7s3dWi or handled dynamically in db setup)
INSERT IGNORE INTO `admin` (`admin_id`, `username`, `password`) VALUES
(1, 'admin', '$2b$10$L1E.R4QxN87wI8z/eJ5Q/.x0E7H8jY3yR9H1J.x9kQ3/lG7p7f3Sm');

-- Seed Standard Disease Knowledge Base
INSERT IGNORE INTO `diseases` (`disease_id`, `disease_name`, `description`, `symptoms`, `prevention`, `treatment`, `risk_level`) VALUES
(1, 'Melanoma', 'A serious skin cancer originating in melanocytes.', 'Asymmetrical moles, irregular borders, color variations, diameter > 6mm.', 'Apply broad-spectrum sunscreen SPF 50+, avoid tanning beds, seek annual skin exams.', 'Surgical excision, immunotherapy, targeted therapy.', 'High'),
(2, 'Eczema (Atopic Dermatitis)', 'Chronic inflammatory skin condition causing dry, red, itchy skin patches.', 'Severe itching, red or dry patches, small raised bumps.', 'Moisturize skin daily, avoid harsh detergents and allergens.', 'Topical corticosteroid creams, calcineurin inhibitors.', 'Low'),
(3, 'Psoriasis', 'Autoimmune skin disease causing rapid cell accumulation and silver scales.', 'Red patches with thick silver scales, dry cracked skin, burning sensation.', 'Maintain healthy weight, avoid skin injury and severe stress.', 'Topical treatments, phototherapy, systemic biologics.', 'Moderate'),
(4, 'Acne Vulgaris', 'Plugged hair follicles leading to comedones and pimples.', 'Whiteheads, blackheads, inflammatory papules and pustules.', 'Wash face twice daily with gentle cleanser, use non-comedogenic skin products.', 'Benzoyl peroxide, salicylic acid, topical retinoids.', 'Low'),
(5, 'Basal Cell Carcinoma', 'Common skin cancer starting in the lower layer of epidermis.', 'Pearly or waxy bump, flat flesh-colored or brown scar-like lesion.', 'Daily sun protection, protective clothing, avoid peak sun hours.', 'Excision, Mohs surgery, cryosurgery.', 'Moderate'),
(6, 'Actinic Keratosis', 'Precancerous rough scaly patch caused by years of sun exposure.', 'Rough, dry, or scaly patch of skin, usually less than 1 inch in diameter.', 'Consistent sun protection, wide-brimmed hats.', 'Cryotherapy, topical creams (5-fluorouracil).', 'Moderate');

-- Seed Sample User & Screening Data
INSERT IGNORE INTO `users` (`user_id`, `full_name`, `email`, `phone`, `password`) VALUES
(1, 'Jane Patient', 'jane@example.com', '+1 555-0192', '$2b$10$L1E.R4QxN87wI8z/eJ5Q/.x0E7H8jY3yR9H1J.x9kQ3/lG7p7f3Sm');

INSERT IGNORE INTO `screenings` (`screening_id`, `user_id`, `image_path`, `prediction`, `confidence`, `risk_level`, `recommendation`) VALUES
(101, 1, 'uploads/sample_skin1.jpg', 'Melanoma', 96.50, 'High', 'Consult a dermatologist immediately for formal histological evaluation and clinical dermoscopy.'),
(102, 1, 'uploads/sample_skin2.jpg', 'Eczema', 89.20, 'Low', 'Apply gentle moisturizers twice daily and avoid harsh soaps. Consult doctor if symptoms persist.');
