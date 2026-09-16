const db = require('../config/db');
const axios = require('axios');
const fs = require('fs');
const FormData = require('form-data');
const { generateScreeningPDF } = require('../utils/pdfGenerator');

const AI_SERVICE_URL = process.env.AI_SERVICE_URL || 'http://localhost:8000';

// Handle Image Upload & AI Service Forwarding
exports.uploadAndScreen = async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ message: 'No image file uploaded.' });
    }

    const userId = req.user.userId;
    const relativeImagePath = `uploads/${req.file.filename}`;
    const fullFilePath = req.file.path;

    console.log('[SCREENING] Upload received:', fullFilePath);

    let aiResult = null;

    // Call Python FastAPI microservice
    try {
      console.log('[SCREENING] Calling FastAPI at', `${AI_SERVICE_URL}/predict`);
      const formData = new FormData();
      formData.append('file', fs.createReadStream(fullFilePath));

      const aiResponse = await axios.post(`${AI_SERVICE_URL}/predict`, formData, {
        headers: formData.getHeaders(),
        timeout: 8000
      });

      console.log('[SCREENING] FastAPI response status:', aiResponse.status);
      aiResult = aiResponse.data;
      console.log('[SCREENING] FastAPI accepted:', aiResult.accepted);
      if (aiResult.model_name) {
        console.log('[SCREENING] FastAPI model name:', aiResult.model_name);
      }
      
      // Fetch risk level and recommendation from DB
      const diseaseInfo = await db.query('SELECT risk_level, treatment FROM diseases WHERE LOWER(disease_name) = LOWER(?)', [aiResult.disease_name]);
      if (diseaseInfo && diseaseInfo.length > 0) {
        aiResult.risk_level = diseaseInfo[0].risk_level;
        aiResult.recommendation = diseaseInfo[0].treatment;
      } else {
        // Fallback for unmapped diseases
        aiResult.risk_level = 'Moderate';
        aiResult.recommendation = 'Consult a dermatologist for evaluation.';
      }

      // Handle Rejection by AI Service
      if (aiResult.accepted === false) {
        console.log('[SCREENING] Rejecting image');
        console.log('[SCREENING] Database insertion skipped');
        return res.status(400).json(aiResult);
      }

    } catch (aiErr) {
      console.log('[SCREENING] FastAPI error:', aiErr.message);
      console.error('⚠️ Python AI FastAPI service error:', aiErr.message);
      return res.status(503).json({ 
        message: 'AI screening service is currently unavailable. Please try again later.' 
      });
    }

    // Save Screening record in Database
    console.log('[SCREENING] Creating database record');
    const insertSql = `
      INSERT INTO screenings (user_id, image_path, prediction, confidence, risk_level, recommendation, class_code, probabilities, model_name, inference_device)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `;

    const result = await db.query(insertSql, [
      userId,
      relativeImagePath,
      aiResult.disease_name,
      aiResult.confidence,
      aiResult.risk_level || 'Low',
      aiResult.recommendation,
      aiResult.predicted_class_code || null,
      aiResult.probabilities ? JSON.stringify(aiResult.probabilities) : null,
      aiResult.model_name || null,
      aiResult.device || null
    ]);

    const screeningId = result.insertId;

    res.status(201).json({
      message: 'AI screening complete!',
      screening: {
        screening_id: screeningId,
        user_id: userId,
        image_path: relativeImagePath,
        prediction: aiResult.disease_name,
        confidence: aiResult.confidence,
        risk_level: aiResult.risk_level || 'Low',
        recommendation: aiResult.recommendation,
        class_code: aiResult.predicted_class_code || null,
        probabilities: aiResult.probabilities || {},
        model_name: aiResult.model_name || null,
        inference_device: aiResult.device || null,
        created_at: new Date()
      }
    });

  } catch (err) {
    console.error('Upload Screening Error:', err);
    res.status(500).json({ message: 'Server error while analyzing skin image.' });
  }
};

// Get User Screenings History
exports.getUserScreenings = async (req, res) => {
  try {
    const userId = req.user.userId;
    const screenings = await db.query(
      'SELECT * FROM screenings WHERE user_id = ? ORDER BY created_at DESC',
      [userId]
    );

    res.json(screenings);
  } catch (err) {
    console.error('Get User Screenings Error:', err);
    res.status(500).json({ message: 'Failed to fetch user screening history.' });
  }
};

// Get Single Screening Detail
exports.getScreeningDetail = async (req, res) => {
  try {
    const { id } = req.params;
    const userId = req.user.userId;

    const screenings = await db.query(
      'SELECT * FROM screenings WHERE screening_id = ? AND user_id = ?',
      [id, userId]
    );

    if (screenings.length === 0) {
      return res.status(404).json({ message: 'Screening record not found.' });
    }

    res.json(screenings[0]);
  } catch (err) {
    console.error('Get Screening Detail Error:', err);
    res.status(500).json({ message: 'Error retrieving screening record.' });
  }
};

// Delete Single Screening Record
exports.deleteScreening = async (req, res) => {
  try {
    const { id } = req.params;
    const userId = req.user.userId;

    await db.query('DELETE FROM screenings WHERE screening_id = ? AND user_id = ?', [id, userId]);
    res.json({ message: 'Screening record deleted successfully.' });

  } catch (err) {
    console.error('Delete Screening Error:', err);
    res.status(500).json({ message: 'Failed to delete screening record.' });
  }
};

// Generate PDF Report Download
exports.downloadReportPDF = async (req, res) => {
  try {
    const { id } = req.params;
    const userId = req.user.userId;

    const screenings = await db.query('SELECT * FROM screenings WHERE screening_id = ? AND user_id = ?', [id, userId]);
    if (screenings.length === 0) {
      return res.status(404).json({ message: 'Screening record not found.' });
    }

    const users = await db.query('SELECT full_name, email FROM users WHERE user_id = ?', [userId]);

    generateScreeningPDF(screenings[0], users[0] || {}, res);

  } catch (err) {
    console.error('Download PDF Error:', err);
    res.status(500).json({ message: 'Failed to generate PDF report.' });
  }
};
