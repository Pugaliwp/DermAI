const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const db = require('../config/db');
const { JWT_SECRET } = require('../middleware/auth');

// Register User
exports.register = async (req, res) => {
  try {
    const { full_name, email, phone, password } = req.body;

    if (!full_name || !email || !password) {
      return res.status(400).json({ message: 'Full name, email, and password are required.' });
    }

    // Check existing user
    const existing = await db.query('SELECT user_id FROM users WHERE email = ?', [email]);
    if (existing.length > 0) {
      return res.status(400).json({ message: 'An account with this email already exists.' });
    }

    const hashedPassword = await bcrypt.hash(password, 10);
    const result = await db.query(
      'INSERT INTO users (full_name, email, phone, password) VALUES (?, ?, ?, ?)',
      [full_name, email, phone || null, hashedPassword]
    );

    const userId = result.insertId;
    res.status(201).json({
      message: 'User registered successfully!',
      user: { user_id: userId, full_name, email, phone }
    });

  } catch (err) {
    console.error('Register Error:', err);
    res.status(500).json({ message: 'Server error during registration.' });
  }
};

// Login User
exports.login = async (req, res) => {
  try {
    const { email, password } = req.body;

    if (!email || !password) {
      return res.status(400).json({ message: 'Email and password are required.' });
    }

    const users = await db.query('SELECT * FROM users WHERE email = ?', [email]);
    if (users.length === 0) {
      return res.status(401).json({ message: 'Invalid email or password.' });
    }

    const user = users[0];
    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) {
      return res.status(401).json({ message: 'Invalid email or password.' });
    }

    const token = jwt.sign(
      { userId: user.user_id, email: user.email, role: 'user' },
      JWT_SECRET,
      { expiresIn: '7d' }
    );

    res.json({
      message: 'Login successful!',
      token,
      user: {
        user_id: user.user_id,
        full_name: user.full_name,
        email: user.email,
        phone: user.phone
      }
    });

  } catch (err) {
    console.error('Login Error:', err);
    res.status(500).json({ message: 'Server error during login.' });
  }
};

// Admin Login
exports.adminLogin = async (req, res) => {
  try {
    const { username, password } = req.body;

    if (!username || !password) {
      return res.status(400).json({ message: 'Username and password required.' });
    }

    const admins = await db.query('SELECT * FROM admin WHERE username = ?', [username]);
    if (admins.length === 0) {
      return res.status(401).json({ message: 'Invalid admin credentials.' });
    }

    const admin = admins[0];
    const isMatch = await bcrypt.compare(password, admin.password);
    if (!isMatch) {
      return res.status(401).json({ message: 'Invalid admin credentials.' });
    }

    const token = jwt.sign(
      { adminId: admin.admin_id, username: admin.username, role: 'admin' },
      JWT_SECRET,
      { expiresIn: '24h' }
    );

    res.json({
      message: 'Admin authentication successful!',
      token,
      user: { admin_id: admin.admin_id, username: admin.username }
    });

  } catch (err) {
    console.error('Admin Login Error:', err);
    res.status(500).json({ message: 'Server error during admin login.' });
  }
};

// Update User Profile
exports.updateProfile = async (req, res) => {
  try {
    const userId = req.user.userId;
    const { full_name, phone, password } = req.body;

    if (password) {
      const hashed = await bcrypt.hash(password, 10);
      await db.query('UPDATE users SET full_name = ?, phone = ?, password = ? WHERE user_id = ?', [full_name, phone, hashed, userId]);
    } else {
      await db.query('UPDATE users SET full_name = ?, phone = ? WHERE user_id = ?', [full_name, phone, userId]);
    }

    res.json({ message: 'Profile updated successfully!' });
  } catch (err) {
    console.error('Update Profile Error:', err);
    res.status(500).json({ message: 'Failed to update profile.' });
  }
};
