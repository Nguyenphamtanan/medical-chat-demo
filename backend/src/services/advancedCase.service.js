import axios from "axios";

const ADVANCED_DISCLAIMER =
  "ThÃ´ng tin chá»‰ mang tÃ­nh tham kháº£o, khÃ´ng thay tháº¿ bÃ¡c sÄ©.";

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

const makeStubFullAgentResponse = (payload) => ({
  case_id: payload.case_id || `stub-${Date.now()}`,
  mode: "full_agent",
  plan: [
    "Validate structured advanced case data.",
    "Route likely specialties.",
    "Return safe fallback analysis without calling MedGemma.",
  ],
  selected_specialties: ["general_medicine"],
  fused_probabilities: {
    general_medicine: 0.5,
  },
  pre_specialist_summary: {
    symptoms: payload.symptoms || [],
    query: payload.query || "",
  },
  specialist_outputs: {
    general_medicine: {
      label: "General medicine",
      key_findings: ["Stub mode is enabled; no AI service was called."],
      red_flags: [
        "Seek urgent care for severe pain, shortness of breath, confusion, fainting, or rapidly worsening symptoms.",
      ],
      missing_data: ["Vital signs", "Physical exam", "Relevant labs and imaging"],
      safe_next_steps: ["Contact a clinician for direct assessment."],
    },
  },
  reflection: {
    model_fallback_used: true,
    warnings: [
      "Seek urgent care for severe pain, shortness of breath, confusion, fainting, or rapidly worsening symptoms.",
    ],
    missing_data: ["Vital signs", "Physical exam"],
  },
  safe_summary:
    "Advanced case stub response generated locally. Enable AI_MODE=local or AI_MODE=colab to call /ai/full-agent.",
  medgemma_status: "stub_response_no_ai_service_called",
  disclaimer: ADVANCED_DISCLAIMER,
});

const normalizeFullAgentResponse = (payload, fallbackStatus) => {
  const source = payload?.data && typeof payload.data === "object" ? payload.data : payload;
  return {
    case_id: source?.case_id || `case-${Date.now()}`,
    mode: "full_agent",
    plan: Array.isArray(source?.plan) ? source.plan : [],
    selected_specialties: Array.isArray(source?.selected_specialties)
      ? source.selected_specialties
      : [],
    fused_probabilities:
      source?.fused_probabilities && typeof source.fused_probabilities === "object"
        ? source.fused_probabilities
        : {},
    pre_specialist_summary:
      source?.pre_specialist_summary && typeof source.pre_specialist_summary === "object"
        ? source.pre_specialist_summary
        : {},
    specialist_outputs:
      source?.specialist_outputs && typeof source.specialist_outputs === "object"
        ? source.specialist_outputs
        : {},
    reflection:
      source?.reflection && typeof source.reflection === "object" ? source.reflection : {},
    safe_summary: source?.safe_summary || "",
    medgemma_status: source?.medgemma_status || fallbackStatus || "unknown",
    disclaimer: source?.disclaimer || ADVANCED_DISCLAIMER,
  };
};

export const analyzeAdvancedCase = async (payload) => {
  const aiConfig = getAiConfig();

  if (aiConfig.mode === "stub") {
    return {
      aiConfig,
      aiResponse: makeStubFullAgentResponse(payload),
    };
  }

  if (!aiConfig.url) {
    const error = new Error("COLAB_AI_URL is required when AI_MODE=colab.");
    error.statusCode = 400;
    throw error;
  }

  const aiResult = await axios.post(`${aiConfig.url}/ai/full-agent`, payload, {
    timeout: 180000,
  });

  return {
    aiConfig,
    aiResponse: normalizeFullAgentResponse(
      aiResult.data,
      `${aiConfig.mode}_full_agent_response`
    ),
  };
};
