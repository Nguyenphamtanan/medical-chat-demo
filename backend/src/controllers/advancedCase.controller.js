import AdvancedCase from "../models/AdvancedCase.js";
import { analyzeAdvancedCase } from "../services/advancedCase.service.js";

export const analyzeAdvancedCaseController = async (req, res) => {
  try {
    const payload = req.body || {};

    if (!Array.isArray(payload.symptoms) || payload.symptoms.length === 0) {
      return res.status(400).json({
        message: "At least one symptom is required for advanced case analysis.",
      });
    }

    const { aiConfig, aiResponse } = await analyzeAdvancedCase(payload);

    const savedCase = await AdvancedCase.create({
      userId: req.user._id,
      caseId: aiResponse.case_id,
      requestPayload: {
        ...payload,
        case_id: aiResponse.case_id,
      },
      aiResponse,
      aiMode: aiConfig.mode,
      modelStatus: aiResponse.medgemma_status,
      serviceUrl: aiConfig.url,
      status: "completed",
    });

    return res.json({
      message: "Advanced case analysis completed.",
      data: {
        case: savedCase,
        aiResponse,
      },
    });
  } catch (error) {
    console.error("ADVANCED CASE AI ERROR:", error.response?.data || error.message);

    return res.status(error.statusCode || 500).json({
      message: "Error analyzing advanced case.",
      error: error.response?.data || error.message,
    });
  }
};

export const getAdvancedCaseController = async (req, res) => {
  try {
    const advancedCase = await AdvancedCase.findOne({
      caseId: req.params.caseId,
      userId: req.user._id,
    }).sort({ createdAt: -1 });

    if (!advancedCase) {
      return res.status(404).json({
        message: "Advanced case not found.",
      });
    }

    return res.json({
      data: advancedCase,
    });
  } catch (error) {
    return res.status(500).json({
      message: "Error loading advanced case.",
      error: error.message,
    });
  }
};
