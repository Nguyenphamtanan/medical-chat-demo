import express from "express";
import {
  askMedicalAgent,
  getChatDetail,
  getChatHistory,
} from "../controllers/chat.controller.js";
import { authMiddleware } from "../middlewares/auth.middleware.js";

const router = express.Router();

router.post("/ask", authMiddleware, askMedicalAgent);
router.get("/history", authMiddleware, getChatHistory);
router.get("/:id", authMiddleware, getChatDetail);

export default router;