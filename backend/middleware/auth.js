const jwt = require('jsonwebtoken');

const JWT_SECRET = process.env.JWT_SECRET || 'derm_ai_secret_key_2026_healthcare';

function verifyToken(req, res, next) {
  const authHeader = req.headers['authorization'];
  console.log('--- verifyToken Debug ---');
  console.log('Auth Header:', authHeader);
  if (!authHeader) {
    return res.status(401).json({ message: 'Access denied. Authorization token missing.' });
  }

  const token = authHeader.split(' ')[1];
  console.log('Extracted Token:', token);
  if (!token) {
    return res.status(401).json({ message: 'Malformed authorization token.' });
  }

  try {
    const decoded = jwt.verify(token, JWT_SECRET);
    req.user = decoded;
    next();
  } catch (err) {
    console.error('JWT Verify Error:', err.message);
    return res.status(403).json({ message: 'Invalid or expired session token.' });
  }
}

function verifyAdmin(req, res, next) {
  verifyToken(req, res, () => {
    if (req.user && req.user.role === 'admin') {
      next();
    } else {
      return res.status(403).json({ message: 'Forbidden. Administrator privileges required.' });
    }
  });
}

module.exports = {
  verifyToken,
  verifyAdmin,
  JWT_SECRET
};
