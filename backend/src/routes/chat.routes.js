import express from "express";
import {
  askMedicalAgent,
  createChatMessage,
  getChatDetail,
  getChatHistory,
} from "../controllers/chat.controller.js";
import { authMiddleware } from "../middlewares/auth.middleware.js";
import { chatRateLimit } from "../middlewares/chatRateLimit.middleware.js";

const router = express.Router();

router.post("/", authMiddleware, chatRateLimit, createChatMessage);
router.post("/ask", authMiddleware, chatRateLimit, askMedicalAgent);
router.get("/history", authMiddleware, getChatHistory);
router.get("/:id", authMiddleware, getChatDetail);

export default router;
