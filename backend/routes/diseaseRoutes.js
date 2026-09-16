const express = require('express');
const router = express.Router();
const diseaseController = require('../controllers/diseaseController');

router.get('/', diseaseController.getAllDiseases);
router.get('/:name', diseaseController.getDiseaseByName);

module.exports = router;
