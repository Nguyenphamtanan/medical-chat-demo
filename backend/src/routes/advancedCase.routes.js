import express from "express";
import {
  analyzeAdvancedCaseController,
  getAdvancedCaseController,
} from "../controllers/advancedCase.controller.js";
import { authMiddleware } from "../middlewares/auth.middleware.js";

const router = express.Router();

router.post("/analyze", authMiddleware, analyzeAdvancedCaseController);
router.get("/:caseId", authMiddleware, getAdvancedCaseController);

export default router;
