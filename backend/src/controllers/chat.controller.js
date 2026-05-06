import axios from "axios";
import ChatMessage from "../models/ChatMessage.js";

const MEDICAL_DISCLAIMER =
  "This assistant is for educational triage support only and does not replace a licensed clinician. Seek urgent care for severe or worsening symptoms.";

const SAFE_RESPONSE_KEYS = {
  summary: "",
  possible_related_systems: [],
  possible_explanations: [],
  red_flags: [],
  missing_questions: [],
  recommendation: "",
  severity: "unknown",
  model_status: "unknown",
  disclaimer: MEDICAL_DISCLAIMER,
};

const getAiConfig = () => {
  const mode = (process.env.AI_MODE || "stub").toLowerCase();

  if (!["stub", "local", "colab"].includes(mode)) {
    return { mode: "stub", url: null };
  }

  if (mode === "local") {
    return {
      mode,
      url: (process.env.LOCAL_AI_URL || "http://127.0.0.1:8000").replace(/\/$/, ""),
    };
  }

  if (mode === "colab") {
    return {
      mode,
      url: (process.env.COLAB_AI_URL || "").replace(/\/$/, ""),
    };
  }

  return { mode: "stub", url: null };
};

const makeStubMedicalResponse = (symptoms) => ({
  summary: `You reported: ${symptoms}`,
  possible_related_systems: ["general", "respiratory", "gastrointestinal"],
  possible_explanations: [
    "A mild self-limited illness can cause overlapping symptoms.",
    "Infection, inflammation, stress, dehydration, or medication effects may contribute.",
  ],
  red_flags: [
    "Chest pain, severe shortness of breath, fainting, confusion, blue lips, or severe weakness.",
    "High fever that persists, severe dehydration, severe abdominal pain, or symptoms that rapidly worsen.",
  ],
  missing_questions: [
    "How long have the symptoms been present?",
    "What is your age and do you have pregnancy, chronic disease, or immune suppression?",
    "Do you have fever, pain severity, breathing trouble, vomiting, bleeding, or new medications?",
  ],
  recommendation:
    "Monitor symptoms, rest, hydrate if appropriate, and contact a healthcare professional if symptoms persist, worsen, or concern you. Seek emergency care immediately for any red flags.",
  severity: "low_to_moderate",
  model_status: "stub_response_no_medgemma_called",
  disclaimer: MEDICAL_DISCLAIMER,
});

const normalizeMedicalResponse = (payload, fallbackStatus) => {
  const source = payload?.data && typeof payload.data === "object" ? payload.data : payload;
  const normalized = { ...SAFE_RESPONSE_KEYS };

  for (const key of Object.keys(normalized)) {
    if (source?.[key] !== undefined) {
      normalized[key] = source[key];
    }
  }

  normalized.possible_related_systems = Array.isArray(normalized.possible_related_systems)
    ? normalized.possible_related_systems
    : [];
  normalized.possible_explanations = Array.isArray(normalized.possible_explanations)
    ? normalized.possible_explanations
    : [];
  normalized.red_flags = Array.isArray(normalized.red_flags) ? normalized.red_flags : [];
  normalized.missing_questions = Array.isArray(normalized.missing_questions)
    ? normalized.missing_questions
    : [];
  normalized.disclaimer = normalized.disclaimer || MEDICAL_DISCLAIMER;
  normalized.model_status = normalized.model_status || fallbackStatus || "unknown";

  return normalized;
};

export const askMedicalAgent = async (req, res) => {
  try {
    const { symptoms } = req.body;

    if (!symptoms || !symptoms.trim()) {
      return res.status(400).json({
        message: "Please enter symptoms before asking the assistant.",
      });
    }

    const trimmedSymptoms = symptoms.trim();
    const aiConfig = getAiConfig();
    let aiResponse;

    if (aiConfig.mode === "stub") {
      aiResponse = makeStubMedicalResponse(trimmedSymptoms);
    } else {
      if (!aiConfig.url) {
        return res.status(400).json({
          message: "COLAB_AI_URL is required when AI_MODE=colab.",
        });
      }

      const aiResult = await axios.post(
        `${aiConfig.url}/ai/analyze`,
        { symptoms: trimmedSymptoms },
        { timeout: 120000 }
      );

      aiResponse = normalizeMedicalResponse(
        aiResult.data,
        `${aiConfig.mode}_ai_service_response`
      );
    }

    const savedMessage = await ChatMessage.create({
      userId: req.user._id,
      question: trimmedSymptoms,
      patientInput: {
        symptoms: trimmedSymptoms,
      },
      aiResponse,
      aiMode: aiConfig.mode,
      modelStatus: aiResponse.model_status,
      serviceUrl: aiConfig.url,
    });

    return res.json({
      message: "AI response received.",
      data: {
        chat: savedMessage,
        aiResponse,
      },
    });
  } catch (error) {
    console.error("AI ERROR:", error.response?.data || error.message);

    return res.status(500).json({
      message: "Error calling AI service.",
      error: error.response?.data || error.message,
    });
  }
};

export const getChatHistory = async (req, res) => {
  try {
    const history = await ChatMessage.find({
      userId: req.user._id,
    }).sort({ createdAt: -1 });

    return res.json({
      data: history,
    });
  } catch (error) {
    return res.status(500).json({
      message: "Error loading chat history.",
      error: error.message,
    });
  }
};

export const getChatDetail = async (req, res) => {
  try {
    const chat = await ChatMessage.findOne({
      _id: req.params.id,
      userId: req.user._id,
    });

    if (!chat) {
      return res.status(404).json({
        message: "Chat not found.",
      });
    }

    return res.json({
      data: chat,
    });
  } catch (error) {
    return res.status(500).json({
      message: "Error loading chat detail.",
      error: error.message,
    });
  }
};
