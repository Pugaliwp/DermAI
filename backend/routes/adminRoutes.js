const express = require('express');
const router = express.Router();
const adminController = require('../controllers/adminController');
const { verifyAdmin } = require('../middleware/auth');

router.get('/stats', verifyAdmin, adminController.getAdminStats);
router.delete('/user/:id', verifyAdmin, adminController.deleteUser);
router.delete('/screening/:id', verifyAdmin, adminController.deleteScreeningRecord);

module.exports = router;
