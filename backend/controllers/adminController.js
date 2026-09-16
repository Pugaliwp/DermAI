const db = require('../config/db');

// Get Admin Analytics & Statistics
exports.getAdminStats = async (req, res) => {
  try {
    const userCountRows = await db.query('SELECT COUNT(*) as count FROM users');
    const screeningCountRows = await db.query('SELECT COUNT(*) as count FROM screenings');
    const highRiskRows = await db.query("SELECT COUNT(*) as count FROM screenings WHERE risk_level = 'High'");

    const users = await db.query('SELECT user_id, full_name, email, phone, created_at FROM users ORDER BY created_at DESC');
    
    const screenings = await db.query(`
      SELECT s.*, u.full_name 
      FROM screenings s 
      LEFT JOIN users u ON s.user_id = u.user_id 
      ORDER BY s.created_at DESC
    `);

    // Disease Category Distribution Stats
    const diseaseDist = await db.query(`
      SELECT prediction as disease_name, COUNT(*) as count 
      FROM screenings 
      GROUP BY prediction
    `);

    res.json({
      totalUsers: userCountRows[0]?.count || 0,
      totalScreenings: screeningCountRows[0]?.count || 0,
      highRiskCount: highRiskRows[0]?.count || 0,
      users,
      screenings,
      diseaseDistribution: diseaseDist
    });

  } catch (err) {
    console.error('Admin Stats Error:', err);
    res.status(500).json({ message: 'Failed to generate admin statistics.' });
  }
};

// Admin Delete User
exports.deleteUser = async (req, res) => {
  try {
    const { id } = req.params;
    await db.query('DELETE FROM users WHERE user_id = ?', [id]);
    res.json({ message: 'User account and associated screenings deleted.' });
  } catch (err) {
    console.error('Admin Delete User Error:', err);
    res.status(500).json({ message: 'Failed to delete user.' });
  }
};

// Admin Delete Screening Record
exports.deleteScreeningRecord = async (req, res) => {
  try {
    const { id } = req.params;
    await db.query('DELETE FROM screenings WHERE screening_id = ?', [id]);
    res.json({ message: 'Screening record deleted.' });
  } catch (err) {
    console.error('Admin Delete Screening Error:', err);
    res.status(500).json({ message: 'Failed to delete screening record.' });
  }
};
