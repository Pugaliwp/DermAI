const db = require('../config/db');

// Get All Disease Information Catalog
exports.getAllDiseases = async (req, res) => {
  try {
    const diseases = await db.query('SELECT * FROM diseases ORDER BY disease_name ASC');
    res.json(diseases);
  } catch (err) {
    console.error('Get Diseases Error:', err);
    res.status(500).json({ message: 'Failed to fetch disease information.' });
  }
};

// Get Single Disease Info
exports.getDiseaseByName = async (req, res) => {
  try {
    const { name } = req.params;
    const diseases = await db.query('SELECT * FROM diseases WHERE disease_name = ?', [name]);

    if (diseases.length === 0) {
      return res.status(404).json({ message: 'Disease profile not found.' });
    }

    res.json(diseases[0]);
  } catch (err) {
    console.error('Get Disease By Name Error:', err);
    res.status(500).json({ message: 'Error retrieving disease info.' });
  }
};
