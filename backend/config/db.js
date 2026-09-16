const mysql = require('mysql2/promise');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const fs = require('fs');
const bcrypt = require('bcryptjs');

let dbMode = 'mysql';
let mysqlPool = null;
let sqliteDb = null;

// Initial Database Setup & Auto-Fallback
async function initDatabase() {
  try {
    // Attempt MySQL Connection
    mysqlPool = mysql.createPool({
      host: process.env.DB_HOST || 'localhost',
      user: process.env.DB_USER || 'root',
      password: process.env.DB_PASSWORD || '',
      database: process.env.DB_NAME || 'skin_portal',
      waitForConnections: true,
      connectionLimit: 10,
      queueLimit: 0,
      connectTimeout: 2000
    });

    const conn = await mysqlPool.getConnection();
    conn.release();
    dbMode = 'mysql';
    console.log('✅ Connected to MySQL Database (skin_portal)');
  } catch (err) {
    console.warn('⚠️ MySQL not reachable. Falling back to embedded SQLite database for instant evaluation...');
    dbMode = 'sqlite';
    setupSqliteFallback();
  }
}

function setupSqliteFallback() {
  const dbPath = path.join(__dirname, '..', 'skin_portal.sqlite');
  sqliteDb = new sqlite3.Database(dbPath);

  sqliteDb.serialize(() => {
    sqliteDb.run(`
      CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        phone TEXT,
        password TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `);

    sqliteDb.run(`
      CREATE TABLE IF NOT EXISTS admin (
        admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
      )
    `);

    sqliteDb.run(`
      CREATE TABLE IF NOT EXISTS screenings (
        screening_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        image_path TEXT NOT NULL,
        prediction TEXT NOT NULL,
        confidence REAL NOT NULL,
        risk_level TEXT DEFAULT 'Low',
        recommendation TEXT NOT NULL,
        class_code TEXT,
        probabilities TEXT,
        model_name TEXT,
        inference_device TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `);

    sqliteDb.run(`
      CREATE TABLE IF NOT EXISTS diseases (
        disease_id INTEGER PRIMARY KEY AUTOINCREMENT,
        disease_name TEXT NOT NULL UNIQUE,
        description TEXT NOT NULL,
        symptoms TEXT NOT NULL,
        prevention TEXT NOT NULL,
        treatment TEXT NOT NULL,
        risk_level TEXT DEFAULT 'Moderate'
      )
    `);

    // Seed default admin (admin / admin123)
    const hashedPass = bcrypt.hashSync('admin123', 10);
    sqliteDb.run(`INSERT OR IGNORE INTO admin (admin_id, username, password) VALUES (1, 'admin', ?)`, [hashedPass]);

    // Seed diseases
    const diseases = [
      ['Melanoma', 'The most serious type of skin cancer originating in melanocytes.', 'Asymmetrical moles, irregular borders, color variations, diameter > 6mm.', 'Apply SPF 50+ sunscreen, avoid UV beds.', 'Surgical excision, immunotherapy.', 'High'],
      ['Eczema (Atopic Dermatitis)', 'Chronic inflammatory skin condition causing dry red patches.', 'Severe itching, red dry patches, small raised bumps.', 'Moisturize daily, avoid harsh soaps.', 'Topical corticosteroid creams.', 'Low'],
      ['Psoriasis', 'Autoimmune skin disease causing silver scale accumulation.', 'Red patches with thick silver scales, dry skin.', 'Maintain healthy weight, avoid skin injuries.', 'Topical creams, phototherapy.', 'Moderate'],
      ['Acne Vulgaris', 'Plugged hair follicles leading to comedones and pimples.', 'Whiteheads, blackheads, inflammatory papules.', 'Wash face twice daily with gentle cleanser.', 'Benzoyl peroxide, salicylic acid.', 'Low'],
      ['Basal Cell Carcinoma', 'Common skin cancer starting in the lower layer of epidermis.', 'Pearly or waxy bump, flat flesh-colored lesion.', 'Daily sun protection, protective clothing.', 'Excision, Mohs surgery.', 'Moderate']
    ];

    diseases.forEach(d => {
      sqliteDb.run(
        `INSERT OR IGNORE INTO diseases (disease_name, description, symptoms, prevention, treatment, risk_level) VALUES (?, ?, ?, ?, ?, ?)`,
        d
      );
    });

    // Seed initial demo user & screening
    sqliteDb.run(
      `INSERT OR IGNORE INTO users (user_id, full_name, email, phone, password) VALUES (1, 'Jane Patient', 'jane@example.com', '+1 555-0192', ?)`,
      [hashedPass]
    );

    sqliteDb.run(
      `INSERT OR IGNORE INTO screenings (screening_id, user_id, image_path, prediction, confidence, risk_level, recommendation) VALUES (101, 1, 'uploads/sample_skin1.jpg', 'Melanoma', 96.50, 'High', 'Consult a dermatologist immediately for formal evaluation.')`
    );

    console.log('✅ SQLite Fallback Database Ready & Seeded.');
  });
}

// Unified Query Execution Abstraction
async function query(sql, params = []) {
  if (dbMode === 'mysql') {
    const [rows] = await mysqlPool.execute(sql, params);
    return rows;
  } else {
    return new Promise((resolve, reject) => {
      const isSelect = sql.trim().toUpperCase().startsWith('SELECT');
      if (isSelect) {
        sqliteDb.all(sql, params, (err, rows) => {
          if (err) reject(err);
          else resolve(rows);
        });
      } else {
        sqliteDb.run(sql, params, function (err) {
          if (err) reject(err);
          else resolve({ insertId: this.lastID, affectedRows: this.changes });
        });
      }
    });
  }
}

module.exports = {
  initDatabase,
  query
};
