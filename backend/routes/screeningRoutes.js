const express = require('express');
const router = express.Router();
const screeningController = require('../controllers/screeningController');
const { verifyToken } = require('../middleware/auth');
const upload = require('../middleware/upload');

router.post('/upload', verifyToken, upload.single('image'), screeningController.uploadAndScreen);
router.get('/user-screenings', verifyToken, screeningController.getUserScreenings);
router.get('/report/:id', verifyToken, screeningController.downloadReportPDF);
router.get('/:id', verifyToken, screeningController.getScreeningDetail);
router.delete('/:id', verifyToken, screeningController.deleteScreening);

module.exports = router;
