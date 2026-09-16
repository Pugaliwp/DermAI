const jwt = require('jsonwebtoken');

const JWT_SECRET = process.env.JWT_SECRET || 'derm_ai_secret_key_2026_healthcare';

function verifyToken(req, res, next) {
  const authHeader = req.headers['authorization'];
  if (!authHeader) {
    return res.status(401).json({ message: 'Access denied. Authorization token missing.' });
  }

  const token = authHeader.split(' ')[1];
  if (!token) {
    return res.status(401).json({ message: 'Malformed authorization token.' });
  }

  try {
    const decoded = jwt.verify(token, JWT_SECRET);
    req.user = decoded;
    next();
  } catch (err) {
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
