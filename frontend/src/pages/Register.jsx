import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import axiosClient from "../api/axiosClient";

export default function Register() {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    fullName: "",
    email: "",
    password: "",
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (e) => {
    setForm({
      ...form,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const res = await axiosClient.post("/auth/register", form);

      localStorage.setItem("token", res.data.token);
      localStorage.setItem("user", JSON.stringify(res.data.user));

      navigate("/chat");
    } catch (err) {
      setError(err.response?.data?.message || "Đăng ký thất bại");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={handleSubmit}>
        <h1>Đăng ký</h1>
        <p>Tạo tài khoản để sử dụng hệ thống hỏi đáp y tế.</p>

        {error && <div className="error">{error}</div>}

        <label>Họ tên</label>
        <input
          name="fullName"
          value={form.fullName}
          onChange={handleChange}
          placeholder="Nguyễn Văn A"
        />

        <label>Email</label>
        <input
          name="email"
          value={form.email}
          onChange={handleChange}
          placeholder="email@gmail.com"
        />

        <label>Mật khẩu</label>
        <input
          name="password"
          type="password"
          value={form.password}
          onChange={handleChange}
          placeholder="••••••••"
        />

        <button disabled={loading}>
          {loading ? "Đang đăng ký..." : "Đăng ký"}
        </button>

        <span>
          Đã có tài khoản? <Link to="/login">Đăng nhập</Link>
        </span>
      </form>
    </div>
  );
}