import express from "express";
import cors from "cors";
import dotenv from "dotenv";
import { connectDB } from "./config/db.js";
import advancedCaseRoutes from "./routes/advancedCase.routes.js";
import authRoutes from "./routes/auth.routes.js";
import chatRoutes from "./routes/chat.routes.js";

dotenv.config();

const app = express();

app.use(cors());
app.use(express.json());

connectDB();

app.get("/", (req, res) => {
  res.json({
    message: "Medical Chat Backend API is running",
  });
});

app.use("/api/auth", authRoutes);
app.use("/api/chat", chatRoutes);
app.use("/api/advanced-case", advancedCaseRoutes);

const PORT = process.env.PORT || 5000;

console.log("AI_MODE =", process.env.AI_MODE);
console.log("COLAB_AI_URL =", process.env.COLAB_AI_URL);
console.log("LOCAL_AI_URL =", process.env.LOCAL_AI_URL);

app.listen(PORT, () => {
  console.log(`Backend running on port ${PORT}`);
});
