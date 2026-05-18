const buckets = new Map();

const WINDOW_MS = 60 * 1000;
const MAX_REQUESTS = 20;

const getClientKey = (req) => {
  const userId = req.user?._id?.toString();
  return userId || req.ip || req.headers["x-forwarded-for"] || "anonymous";
};

export const chatRateLimit = (req, res, next) => {
  const key = getClientKey(req);
  const now = Date.now();
  const current = buckets.get(key);

  if (!current || current.resetAt <= now) {
    buckets.set(key, {
      count: 1,
      resetAt: now + WINDOW_MS,
    });
    return next();
  }

  if (current.count >= MAX_REQUESTS) {
    return res.status(429).json({
      message: "Too many chat requests. Please wait a minute and try again.",
    });
  }

  current.count += 1;
  buckets.set(key, current);
  return next();
};
