"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { RequireAuth } from "@/components/RequireAuth";
import { BottomSheet } from "@/components/BottomSheet";
import { MediaUploader } from "@/components/MediaUploader";
import { useToast } from "@/components/ToastProvider";
import {
  DISASTER_TYPES,
  LEVELS,
  getDisasterType,
  getLevel,
} from "@/lib/constants";
import { submitReport } from "@/lib/api";
import { addRecentReport, getDraft, setDraft, clearDraft, type ReportDraft } from "@/lib/storage";
import type { ReportPayload } from "@/lib/types";

function ReportInner() {
  const { toast } = useToast();
  const [title, setTitle] = useState("");
  const [type, setType] = useState("");
  const [level, setLevel] = useState("");
  const [content, setContent] = useState("");
  const [locationText, setLocationText] = useState("");
  const [lat, setLat] = useState<number>(0);
  const [lng, setLng] = useState<number>(0);
  const [contact, setContact] = useState("");
  const [images, setImages] = useState("");
  const [typeOpen, setTypeOpen] = useState(false);
  const [levelOpen, setLevelOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [locating, setLocating] = useState(false);
  const [submitted, setSubmitted] = useState<{ code?: string; title: string } | null>(null);
  const [errors, setErrors] = useState<Record<string, boolean>>({});
  const [draftSavedAt, setDraftSavedAt] = useState<number | null>(null);
  const savedRef = useRef(false);

  // 进入页面时回填草稿
  useEffect(() => {
    const d = getDraft();
    if (d) {
      setTitle(d.title);
      setType(d.type);
      setLevel(d.level);
      setContent(d.content);
      setLocationText(d.locationText);
      setContact(d.contact);
      setImages(d.images);
      setDraftSavedAt(d.savedAt);
    }
  }, []);

  // 表单变化自动存草稿（提交成功后清除）
  useEffect(() => {
    if (submitted || savedRef.current) return;
    const t = setTimeout(() => {
      if (title || type || level || content || locationText || contact || images) {
        setDraft({ title, type, level, content, locationText, contact, images });
        setDraftSavedAt(Date.now());
      }
    }, 800);
    return () => clearTimeout(t);
  }, [title, type, level, content, locationText, contact, images, submitted]);

  function getLocation() {
    if (typeof navigator === "undefined" || !navigator.geolocation) {
      toast("当前设备不支持定位", "error");
      return;
    }
    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const { latitude, longitude } = pos.coords;
        setLat(latitude);
        setLng(longitude);
        setLocationText((prev) => prev || `${latitude.toFixed(6)}, ${longitude.toFixed(6)}`);
        setLocating(false);
        toast("定位成功", "success");
      },
      (err) => {
        setLocating(false);
        toast(`定位失败：${err.message}`, "error");
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const errs: Record<string, boolean> = {
      title: !title.trim(),
      type: !type,
      level: !level,
      content: !content.trim(),
    };
    setErrors(errs);
    if (Object.values(errs).some(Boolean)) {
      toast("请完善带 * 的必填项", "error");
      return;
    }

    const payload: ReportPayload = {
      title: title.trim(),
      type,
      level,
      content: content.trim(),
      locationText: locationText.trim(),
      lat,
      lng,
      images,
      contact: contact.trim(),
    };

    setSubmitting(true);
    try {
      const record = await submitReport(payload);
      savedRef.current = true;
      clearDraft();
      addRecentReport({
        id: record.id,
        code: record.code,
        title: record.title,
        type: record.type,
        level: record.level,
        status: record.status ?? "PENDING_VERIFY",
        createdAt: record.createdAt ?? new Date().toISOString(),
      });
      setSubmitted({ code: record.code, title: record.title });
    } catch (err) {
      toast(err instanceof Error ? err.message : "上报失败", "error");
    } finally {
      setSubmitting(false);
    }
  }

  function resetForm() {
    setTitle("");
    setType("");
    setLevel("");
    setContent("");
    setLocationText("");
    setLat(0);
    setLng(0);
    setContact("");
    setImages("");
    setErrors({});
    setSubmitted(null);
    savedRef.current = false;
  }

  const selectedType = getDisasterType(type);
  const selectedLevel = getLevel(level);

  const fieldCls = (bad: boolean) =>
    `w-full h-11 px-3 rounded-xl bg-gray-50 border outline-none transition ${
      bad ? "border-emergency-red ring-1 ring-emergency-red/30" : "border-gray-200 focus:border-emergency-blue"
    }`;

  // 提交成功页
  if (submitted) {
    return (
      <div className="px-4 pt-10 pb-safe flex flex-col items-center text-center">
        <div className="w-20 h-20 rounded-full bg-emergency-blue/10 flex items-center justify-center text-4xl animate-fade-in">
          ✓
        </div>
        <h2 className="mt-5 text-xl font-bold text-gray-800">上报成功</h2>
        <p className="mt-2 text-sm text-gray-500 max-w-xs">
          您的灾情信息已提交，我们将尽快核验并启动响应。
          {submitted.code && <span className="block mt-1 text-gray-400">工单号：{submitted.code}</span>}
        </p>
        <div className="mt-8 w-full space-y-3">
          <button
            onClick={resetForm}
            className="w-full h-12 rounded-xl bg-emergency-red text-white font-semibold active:bg-emergency-red-dark"
          >
            再报一条
          </button>
          <Link
            href="/profile"
            className="block w-full h-12 rounded-xl bg-white border border-gray-200 text-emergency-blue font-semibold flex items-center justify-center active:bg-gray-50"
          >
            查看我的上报
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="px-4 pt-4 pb-safe">
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* 标题 */}
        <div className="bg-white rounded-2xl shadow-card p-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            灾情标题 <span className="text-emergency-red">*</span>
          </label>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="例如：XX村山体滑坡险情"
            className={fieldCls(errors.title)}
          />
          {errors.title && <p className="mt-1 text-xs text-emergency-red">请填写灾情标题</p>}
        </div>

        {/* 灾害类型 + 等级 */}
        <div className="bg-white rounded-2xl shadow-card p-4 grid grid-cols-2 gap-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              灾害类型 <span className="text-emergency-red">*</span>
            </label>
            <button
              type="button"
              onClick={() => setTypeOpen(true)}
              className={`w-full h-11 px-3 rounded-xl bg-gray-50 border flex items-center justify-between ${
                errors.type ? "border-emergency-red ring-1 ring-emergency-red/30" : "border-gray-200"
              }`}
            >
              <span className={selectedType ? "text-gray-800" : "text-gray-400"}>
                {selectedType ? `${selectedType.icon} ${selectedType.label}` : "请选择"}
              </span>
              <span className="text-gray-400">▾</span>
            </button>
            {errors.type && <p className="mt-1 text-xs text-emergency-red">请选择灾害类型</p>}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              灾害等级 <span className="text-emergency-red">*</span>
            </label>
            <button
              type="button"
              onClick={() => setLevelOpen(true)}
              className={`w-full h-11 px-3 rounded-xl bg-gray-50 border flex items-center justify-between ${
                errors.level ? "border-emergency-red ring-1 ring-emergency-red/30" : "border-gray-200"
              }`}
            >
              <span className={selectedLevel ? "text-gray-800" : "text-gray-400"}>
                {selectedLevel ? `${selectedLevel.roman} ${selectedLevel.label}` : "请选择"}
              </span>
              <span className="text-gray-400">▾</span>
            </button>
            {errors.level && <p className="mt-1 text-xs text-emergency-red">请选择灾害等级</p>}
          </div>
        </div>

        {/* 灾情描述 */}
        <div className="bg-white rounded-2xl shadow-card p-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            灾情描述 <span className="text-emergency-red">*</span>
          </label>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="请描述灾情形势、规模、受影响范围、人员伤亡与转移情况等"
            rows={4}
            className={`w-full px-3 py-2.5 rounded-xl bg-gray-50 border outline-none resize-none transition ${
              errors.content ? "border-emergency-red ring-1 ring-emergency-red/30" : "border-gray-200 focus:border-emergency-blue"
            }`}
          />
          {errors.content && <p className="mt-1 text-xs text-emergency-red">请填写灾情描述</p>}
        </div>

        {/* 位置 */}
        <div className="bg-white rounded-2xl shadow-card p-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">发生位置</label>
          <input
            value={locationText}
            onChange={(e) => setLocationText(e.target.value)}
            placeholder="如：云南省XX市XX县XX镇XX村"
            className="w-full h-11 px-3 rounded-xl bg-gray-50 border border-gray-200 outline-none focus:border-emergency-blue"
          />
          <div className="mt-2 flex items-center justify-between text-xs text-gray-500">
            <span>经纬度：{lat || lng ? `${lat.toFixed(6)}, ${lng.toFixed(6)}` : "未获取"}</span>
            <button
              type="button"
              onClick={getLocation}
              disabled={locating}
              className="flex items-center gap-1 px-3 h-9 rounded-lg bg-emergency-blue/10 text-emergency-blue font-medium disabled:opacity-60"
            >
              📍 {locating ? "定位中…" : "获取定位"}
            </button>
          </div>
        </div>

        {/* 联系电话 */}
        <div className="bg-white rounded-2xl shadow-card p-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">联系电话</label>
          <input
            value={contact}
            onChange={(e) => setContact(e.target.value)}
            placeholder="便于核实灾情的联系方式"
            inputMode="tel"
            className="w-full h-11 px-3 rounded-xl bg-gray-50 border border-gray-200 outline-none focus:border-emergency-blue"
          />
        </div>

        {/* 媒体上传 */}
        <div className="bg-white rounded-2xl shadow-card p-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">现场图片 / 视频</label>
          <p className="text-xs text-gray-400 mb-3">支持拍照、录像或从相册选择，自动上传到 /api/upload</p>
          <MediaUploader value={images} onChange={setImages} />
        </div>

        {draftSavedAt && !submitted && (
          <p className="text-center text-xs text-gray-400">草稿已自动保存</p>
        )}

        <button
          type="submit"
          disabled={submitting}
          className="w-full h-12 rounded-xl bg-emergency-red text-white font-semibold text-base active:bg-emergency-red-dark disabled:opacity-60"
        >
          {submitting ? "上报中…" : "提交上报"}
        </button>
      </form>

      {/* 灾害类型选择弹层 */}
      <BottomSheet open={typeOpen} onClose={() => setTypeOpen(false)} title="选择灾害类型">
        <div className="grid grid-cols-2 gap-3">
          {DISASTER_TYPES.map((t) => (
            <button
              key={t.value}
              type="button"
              onClick={() => {
                setType(t.value);
                setTypeOpen(false);
              }}
              className={`flex items-center gap-2 px-3 h-12 rounded-xl border ${
                type === t.value ? "border-emergency-blue bg-emergency-blue/10 text-emergency-blue" : "border-gray-200 text-gray-700"
              }`}
            >
              <span className="text-xl">{t.icon}</span>
              <span className="font-medium">{t.label}</span>
            </button>
          ))}
        </div>
      </BottomSheet>

      {/* 等级选择弹层 */}
      <BottomSheet open={levelOpen} onClose={() => setLevelOpen(false)} title="选择灾害等级">
        <div className="space-y-3">
          {LEVELS.map((l) => (
            <button
              key={l.value}
              type="button"
              onClick={() => {
                setLevel(l.value);
                setLevelOpen(false);
              }}
              className={`w-full flex items-center justify-between px-4 h-14 rounded-xl border ${
                level === l.value ? "border-emergency-blue bg-emergency-blue/10" : "border-gray-200"
              }`}
            >
              <span className="flex items-center gap-3">
                <span className={`px-2.5 py-1 rounded-full text-sm font-bold ${l.badge}`}>{l.roman}</span>
                <span className="font-medium text-gray-800">{l.label}</span>
              </span>
              {level === l.value && <span className="text-emergency-blue">✓</span>}
            </button>
          ))}
        </div>
      </BottomSheet>
    </div>
  );
}

export default function ReportPage() {
  return (
    <RequireAuth>
      <ReportInner />
    </RequireAuth>
  );
}
