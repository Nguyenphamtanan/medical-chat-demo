import mongoose from "mongoose";

const advancedCaseSchema = new mongoose.Schema(
  {
    userId: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "User",
      required: true,
    },
    caseId: {
      type: String,
      required: true,
      index: true,
    },
    requestPayload: {
      type: Object,
      required: true,
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
    status: {
      type: String,
      enum: ["completed", "failed"],
      default: "completed",
    },
  },
  { timestamps: true }
);

advancedCaseSchema.index({ userId: 1, caseId: 1 });

export default mongoose.model("AdvancedCase", advancedCaseSchema);
