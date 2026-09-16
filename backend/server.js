const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs');
const { initDatabase } = require('./config/db');

const app = express();
const PORT = process.env.PORT || 5000;

// Ensure uploads folder exists
const uploadsDir = path.join(__dirname, 'uploads');
if (!fs.existsSync(uploadsDir)) {
  fs.mkdirSync(uploadsDir, { recursive: true });
}

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Serve Uploaded Lesion Files & Frontend Web Assets
app.use('/uploads', express.static(path.join(__dirname, 'uploads')));
app.use(express.static(path.join(__dirname, '..', 'frontend')));

// Initialize Database Connection
initDatabase();

// Health Check API
app.get('/api/health', (req, res) => {
  res.json({
    status: 'online',
    app: 'AI Skin Health Screening Portal',
    timestamp: new Date()
  });
});

// Import & Register REST API Routes
const authRoutes = require('./routes/authRoutes');
const screeningRoutes = require('./routes/screeningRoutes');
const diseaseRoutes = require('./routes/diseaseRoutes');
const adminRoutes = require('./routes/adminRoutes');

app.use('/api/auth', authRoutes);
app.use('/api/screening', screeningRoutes);
app.use('/api/diseases', diseaseRoutes);
app.use('/api/admin', adminRoutes);

// Global Fallback for Single Page App / Frontend routing
app.get('*', (req, res) => {
  const frontendIndex = path.join(__dirname, '..', 'frontend', 'index.html');
  if (fs.existsSync(frontendIndex)) {
    res.sendFile(frontendIndex);
  } else {
    res.status(404).send('Frontend static files not found.');
  }
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error('Unhandled Global Error:', err.message);
  res.status(500).json({ message: err.message || 'Internal Server Error' });
});

app.listen(PORT, () => {
  console.log(`===================================================`);
  console.log(`🚀 DermAI Express Backend running on port ${PORT}`);
  console.log(`🌐 Frontend Portal: http://localhost:${PORT}`);
  console.log(`===================================================`);
});
