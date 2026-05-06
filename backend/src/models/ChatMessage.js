import mongoose from "mongoose";

const chatMessageSchema = new mongoose.Schema(
  {
    userId: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "User",
      required: true,
    },
    question: {
      type: String,
      required: true,
    },
    patientInput: {
      symptoms: {
        type: String,
        required: true,
      },
    },
    aiResponse: {
      type: Object,
      required: true,
    },
    aiMode: {
      type: String,
      enum: ["stub", "local", "colab"],
      default: "stub",
    },
    modelStatus: {
      type: String,
      default: "unknown",
    },
    serviceUrl: {
      type: String,
      default: null,
    },
  },
  { timestamps: true }
);

export default mongoose.model("ChatMessage", chatMessageSchema);
