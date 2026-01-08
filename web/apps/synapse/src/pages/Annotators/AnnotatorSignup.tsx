import React, { useState } from "react";
import { useHistory } from "react-router-dom";
import { Button, useToast, ToastType } from "@synapse/ui";
import "./AnnotatorSignup.css";

interface FormData {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
  confirm_password: string;
  phone: string;
  skills: string[];
  languages: string[];
  experience_level: string;
  bio: string;
}

export const AnnotatorSignup = () => {
  const history = useHistory();
  const toast = useToast();

  const [formData, setFormData] = useState<FormData>({
    first_name: "",
    last_name: "",
    email: "",
    password: "",
    confirm_password: "",
    phone: "",
    skills: [],
    languages: [],
    experience_level: "beginner",
    bio: "",
  });

  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(1); // 1: Basic Info, 2: Skills & Experience

  const skillOptions = [
    "Image Classification",
    "Object Detection",
    "Text Classification",
    "Named Entity Recognition",
    "Text Summarization",
    "Audio Transcription",
    "Video Annotation",
    "Semantic Segmentation",
  ];

  const languageOptions = [
    "English",
    "Hindi",
    "Spanish",
    "French",
    "German",
    "Chinese",
    "Japanese",
    "Arabic",
  ];

  const handleInputChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement
    >
  ) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleSkillToggle = (skill: string) => {
    const skills = formData.skills.includes(skill)
      ? formData.skills.filter((s) => s !== skill)
      : [...formData.skills, skill];
    setFormData({ ...formData, skills });
  };

  const handleLanguageToggle = (language: string) => {
    const languages = formData.languages.includes(language)
      ? formData.languages.filter((l) => l !== language)
      : [...formData.languages, language];
    setFormData({ ...formData, languages });
  };

  const validateStep1 = () => {
    if (!formData.first_name || !formData.last_name) {
      toast?.show({
        message: "Please enter your full name",
        type: ToastType.error,
        duration: 3000,
      });
      return false;
    }
    if (!formData.email || !/\S+@\S+\.\S+/.test(formData.email)) {
      toast?.show({
        message: "Please enter a valid email address",
        type: ToastType.error,
        duration: 3000,
      });
      return false;
    }
    if (!formData.password || formData.password.length < 8) {
      toast?.show({
        message: "Password must be at least 8 characters",
        type: ToastType.error,
        duration: 3000,
      });
      return false;
    }
    if (formData.password !== formData.confirm_password) {
      toast?.show({
        message: "Passwords do not match",
        type: ToastType.error,
        duration: 3000,
      });
      return false;
    }
    if (
      !formData.phone ||
      !/^\d{10}$/.test(formData.phone.replace(/[-\s]/g, ""))
    ) {
      toast?.show({
        message: "Please enter a valid 10-digit phone number",
        type: ToastType.error,
        duration: 3000,
      });
      return false;
    }
    return true;
  };

  const validateStep2 = () => {
    if (formData.skills.length === 0) {
      toast?.show({
        message: "Please select at least one skill",
        type: ToastType.error,
        duration: 3000,
      });
      return false;
    }
    if (formData.languages.length === 0) {
      toast?.show({
        message: "Please select at least one language",
        type: ToastType.error,
        duration: 3000,
      });
      return false;
    }
    return true;
  };

  const handleNext = () => {
    if (validateStep1()) {
      setStep(2);
    }
  };

  const isStep2Valid = () => {
    return formData.skills.length > 0 && formData.languages.length > 0;
  };

  const validateStep2WithToast = () => {
    if (formData.skills.length === 0) {
      toast?.show({
        message: "Please select at least one skill",
        type: ToastType.error,
        duration: 3000,
      });
      return false;
    }

    if (formData.languages.length === 0) {
      toast?.show({
        message: "Please select at least one language",
        type: ToastType.error,
        duration: 3000,
      });
      return false;
    }

    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateStep2WithToast()) return;

    setLoading(true);

    const payload = {
      first_name: formData.first_name,
      last_name: formData.last_name,
      email: formData.email,
      password: formData.password,
      phone: formData.phone.replace(/\D/g, ""),
      skills: formData.skills,
      languages: formData.languages,
      experience_level: formData.experience_level,
      bio: formData.bio,
    };

    try {
      const response = await fetch("/api/annotators/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (response.ok) {
        toast?.show({
          message:
            "Registration successful! Please check your email to verify your account.",
          type: ToastType.info,
          duration: 6000,
        });

        // Redirect to verification status page
        setTimeout(() => {
          history.push("/annotators/verification-sent", {
            email: formData.email,
          });
        }, 2000);
      } else {
        toast?.show({
          message:
            data.error ||
            data.email?.[0] ||
            "Registration failed. Please try again.",
          type: ToastType.error,
          duration: 5000,
        });
      }
    } catch (error) {
      console.error("Registration error:", error);
      toast?.show({
        message: "An error occurred. Please try again later.",
        type: ToastType.error,
        duration: 5000,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="annotator-signup-container">
      <div className="annotator-signup-card">
        <div className="signup-header">
          <h1>Join as an Annotator</h1>
          <p>Help improve AI by providing high-quality annotations</p>
        </div>

        <div className="progress-indicator">
          <div
            className={`progress-step ${step >= 1 ? "active" : ""} ${
              step > 1 ? "completed" : ""
            }`}
          >
            <div className="step-circle">1</div>
            <span>Basic Info</span>
          </div>
          <div className="progress-line"></div>
          <div className={`progress-step ${step >= 2 ? "active" : ""}`}>
            <div className="step-circle">2</div>
            <span>Skills & Experience</span>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="signup-form">
          {step === 1 && (
            <div className="form-step">
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="first_name">First Name *</label>
                  <input
                    type="text"
                    id="first_name"
                    name="first_name"
                    value={formData.first_name}
                    onChange={handleInputChange}
                    required
                    placeholder="Enter your first name"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="last_name">Last Name *</label>
                  <input
                    type="text"
                    id="last_name"
                    name="last_name"
                    value={formData.last_name}
                    onChange={handleInputChange}
                    required
                    placeholder="Enter your last name"
                  />
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="email">Email *</label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  required
                  placeholder="your.email@example.com"
                />
              </div>

              <div className="form-group">
                <label htmlFor="phone">Phone Number *</label>
                <input
                  type="tel"
                  id="phone"
                  name="phone"
                  value={formData.phone}
                  onChange={handleInputChange}
                  required
                  placeholder="1234567890"
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="password">Password *</label>
                  <input
                    type="password"
                    id="password"
                    name="password"
                    value={formData.password}
                    onChange={handleInputChange}
                    required
                    placeholder="At least 8 characters"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="confirm_password">Confirm Password *</label>
                  <input
                    type="password"
                    id="confirm_password"
                    name="confirm_password"
                    value={formData.confirm_password}
                    onChange={handleInputChange}
                    required
                    placeholder="Re-enter password"
                  />
                </div>
              </div>

              <div className="form-actions">
                <Button
                  type="button"
                  onClick={() => history.push("/annotators/login")}
                  style={{
                    minWidth: "120px",
                    backgroundColor: "#f3f4f6",
                    color: "#374151",
                  }}
                >
                  Back to Login
                </Button>
                <Button
                  type="button"
                  onClick={handleNext}
                  style={{ minWidth: "120px", backgroundColor: "#3b82f6" }}
                >
                  Next
                </Button>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="form-step">
              <div className="form-group">
                <label>Annotation Skills * (Select all that apply)</label>
                <div className="skill-tags">
                  {skillOptions.map((skill) => (
                    <button
                      key={skill}
                      type="button"
                      className={`skill-tag ${
                        formData.skills.includes(skill) ? "selected" : ""
                      }`}
                      onClick={() => handleSkillToggle(skill)}
                    >
                      {skill}
                    </button>
                  ))}
                </div>
              </div>

              <div className="form-group">
                <label>Languages * (Select all that apply)</label>
                <div className="skill-tags">
                  {languageOptions.map((language) => (
                    <button
                      key={language}
                      type="button"
                      className={`skill-tag ${
                        formData.languages.includes(language) ? "selected" : ""
                      }`}
                      onClick={() => handleLanguageToggle(language)}
                    >
                      {language}
                    </button>
                  ))}
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="experience_level">Experience Level *</label>
                <select
                  id="experience_level"
                  name="experience_level"
                  value={formData.experience_level}
                  onChange={handleInputChange}
                  required
                >
                  <option value="beginner">Beginner (0-1 years)</option>
                  <option value="intermediate">Intermediate (1-3 years)</option>
                  <option value="expert">Expert (3+ years)</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="bio">Brief Introduction (Optional)</label>
                <textarea
                  id="bio"
                  name="bio"
                  value={formData.bio}
                  onChange={handleInputChange}
                  placeholder="Tell us a bit about yourself and your experience..."
                  rows={4}
                />
              </div>

              <div className="form-actions">
                <Button
                  type="button"
                  onClick={() => setStep(1)}
                  style={{
                    minWidth: "120px",
                    backgroundColor: "#f3f4f6",
                    color: "#374151",
                  }}
                >
                  Back
                </Button>
                <Button
                  type="submit"
                  disabled={loading || !isStep2Valid()}
                  waiting={loading}
                  style={{ minWidth: "120px", backgroundColor: "#10b981" }}
                >
                  {loading ? "Creating Account..." : "Create Account"}
                </Button>
              </div>
            </div>
          )}
        </form>

        <div className="signup-footer">
          <p>
            Already have an account?{" "}
            <a
              href="/annotators/login"
              onClick={(e) => {
                e.preventDefault();
                history.push("/annotators/login");
              }}
            >
              Log in
            </a>
          </p>
        </div>
      </div>
    </div>
  );
};

