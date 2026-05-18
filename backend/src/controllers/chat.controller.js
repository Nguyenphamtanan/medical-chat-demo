import axios from "axios";
import mongoose from "mongoose";
import ChatMessage from "../models/ChatMessage.js";
import Conversation from "../models/Conversation.js";
import Message from "../models/Message.js";

const MEDICAL_DISCLAIMER =
  "Thông tin chỉ mang tính tham khảo, không thay thế bác sĩ. Nếu có dấu hiệu nặng hoặc triệu chứng xấu đi, hãy đi khám hoặc cấp cứu.";

const FAST_TIMEOUT_MS = 90 * 1000;
const FULL_TIMEOUT_MS = 180 * 1000;
const HISTORY_LIMIT = 8;

const getAiConfig = () => {
  const directUrl = (process.env.AI_SERVICE_URL || "").replace(/\/$/, "");

  if (directUrl) {
    return {
      mode: "service",
      url: directUrl,
    };
  }

  const mode = (process.env.AI_MODE || "stub").toLowerCase();

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

const makeTitle = (message) => {
  const clean = message.replace(/\s+/g, " ").trim();
  return clean.length > 60 ? `${clean.slice(0, 57)}...` : clean || "New medical chat";
};

const validateChatBody = (body) => {
  const message = body?.message;
  const mode = body?.mode || "fast";

  if (typeof message !== "string") {
    return { error: "message is required and must be a string." };
  }

  const trimmedMessage = message.trim();

  if (!trimmedMessage) {
    return { error: "message must not be empty." };
  }

  if (trimmedMessage.length > 3000) {
    return { error: "message must be 3000 characters or fewer." };
  }

  if (!["fast", "full"].includes(mode)) {
    return { error: 'mode must be either "fast" or "full".' };
  }

  return {
    value: {
      conversationId: body?.conversationId,
      message: trimmedMessage,
      mode,
    },
  };
};

const normalizeFastAiResponse = (payload, fallbackStatus) => {
  const source = payload?.data && typeof payload.data === "object" ? payload.data : payload;
  const answer =
    source?.answer ||
    source?.summary ||
    source?.recommendation ||
    "Mình chưa tạo được câu trả lời rõ ràng. Bạn có thể mô tả thêm triệu chứng, thời gian xuất hiện và mức độ nặng không?";

  return {
    content: answer,
    metadata: {
      mode: "fast",
      modelStatus: source?.model_status || source?.modelStatus || fallbackStatus || "unknown",
      aiRaw: source || null,
    },
  };
};

const normalizeFullAiResponse = (payload, fallbackStatus) => {
  const source = payload?.data && typeof payload.data === "object" ? payload.data : payload;
  const content =
    source?.safe_summary ||
    source?.answer ||
    "Deep analysis mode completed, but the AI service did not return a summary.";

  return {
    content: `[Phân tích chuyên sâu] ${content}`,
    metadata: {
      mode: "full",
      modelStatus: source?.medgemma_status || source?.model_status || fallbackStatus || "unknown",
      aiRaw: source || null,
    },
  };
};

const makeStubChatResponse = (message, mode) => ({
  content:
    mode === "full"
      ? `[Phân tích chuyên sâu] Stub mode đang bật, chưa gọi full-agent. Nội dung người dùng: ${message}`
      : `Mình ghi nhận: ${message}. Hãy đi khám/cấp cứu nếu có khó thở, đau ngực, lơ mơ, ngất, sốt cao kéo dài hoặc triệu chứng xấu đi nhanh.`,
  metadata: {
    mode,
    modelStatus: "stub_response_no_ai_service_called",
    aiRaw: {
      disclaimer: MEDICAL_DISCLAIMER,
    },
  },
});

const getOrCreateConversation = async ({ conversationId, userId, message }) => {
  if (conversationId) {
    if (!mongoose.Types.ObjectId.isValid(conversationId)) {
      const error = new Error("conversationId is invalid.");
      error.statusCode = 400;
      throw error;
    }

    const existingConversation = await Conversation.findOne({
      _id: conversationId,
      userId,
    });

    if (!existingConversation) {
      const error = new Error("Conversation not found.");
      error.statusCode = 404;
      throw error;
    }

    return existingConversation;
  }

  return Conversation.create({
    userId,
    title: makeTitle(message),
  });
};

const buildHistory = async (conversationId) => {
  const recentMessages = await Message.find({ conversationId })
    .sort({ createdAt: -1 })
    .limit(HISTORY_LIMIT)
    .lean();

  return recentMessages
    .reverse()
    .map((item) => ({
      role: item.role,
      content: item.content,
    }));
};

const callAiService = async ({ aiConfig, message, mode, history }) => {
  if (aiConfig.mode === "stub") {
    return makeStubChatResponse(message, mode);
  }

  if (!aiConfig.url) {
    const error = new Error("AI_SERVICE_URL or COLAB_AI_URL is required.");
    error.statusCode = 400;
    throw error;
  }

  if (mode === "full") {
    const aiResult = await axios.post(
      `${aiConfig.url}/ai/full-agent`,
      {
        symptoms: [message],
        history: history.map((item) => `${item.role}: ${item.content}`),
        query: message,
      },
      { timeout: FULL_TIMEOUT_MS }
    );

    return normalizeFullAiResponse(aiResult.data, `${aiConfig.mode}_full_agent_response`);
  }

  const aiResult = await axios.post(
    `${aiConfig.url}/ai/chat`,
    {
      message,
      history,
    },
    { timeout: FAST_TIMEOUT_MS }
  );

  return normalizeFastAiResponse(aiResult.data, `${aiConfig.mode}_fast_chat_response`);
};

export const createChatMessage = async (req, res) => {
  try {
    const validation = validateChatBody(req.body);

    if (validation.error) {
      return res.status(400).json({
        message: validation.error,
      });
    }

    const { conversationId, message, mode } = validation.value;
    const conversation = await getOrCreateConversation({
      conversationId,
      userId: req.user._id,
      message,
    });

    await Message.create({
      conversationId: conversation._id,
      userId: req.user._id,
      role: "user",
      content: message,
      metadata: { mode },
    });

    const history = await buildHistory(conversation._id);
    const aiConfig = getAiConfig();
    const assistantResponse = await callAiService({
      aiConfig,
      message,
      mode,
      history,
    });

    const savedAssistantMessage = await Message.create({
      conversationId: conversation._id,
      userId: req.user._id,
      role: "assistant",
      content: assistantResponse.content,
      metadata: assistantResponse.metadata,
    });

    conversation.updatedAt = new Date();
    await conversation.save();

    return res.json({
      conversationId: conversation._id.toString(),
      message: {
        role: savedAssistantMessage.role,
        content: savedAssistantMessage.content,
        metadata: savedAssistantMessage.metadata,
      },
    });
  } catch (error) {
    console.error("CHAT AI ERROR:", error.response?.data || error.message);

    return res.status(error.statusCode || 500).json({
      message: "Error calling AI service.",
      error: error.response?.data || error.message,
    });
  }
};

export const askMedicalAgent = async (req, res) => {
  req.body = {
    conversationId: req.body?.conversationId,
    message: req.body?.message || req.body?.symptoms,
    mode: req.body?.mode || "fast",
  };

  return createChatMessage(req, res);
};

export const getChatHistory = async (req, res) => {
  try {
    const conversations = await Conversation.find({
      userId: req.user._id,
    }).sort({ updatedAt: -1 });

    if (conversations.length > 0) {
      return res.json({
        data: conversations,
      });
    }

    const legacyHistory = await ChatMessage.find({
      userId: req.user._id,
    }).sort({ createdAt: -1 });

    return res.json({
      data: legacyHistory,
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
    if (mongoose.Types.ObjectId.isValid(req.params.id)) {
      const conversation = await Conversation.findOne({
        _id: req.params.id,
        userId: req.user._id,
      });

      if (conversation) {
        const messages = await Message.find({
          conversationId: conversation._id,
          userId: req.user._id,
        }).sort({ createdAt: 1 });

        return res.json({
          data: {
            conversation,
            messages,
          },
        });
      }
    }

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
