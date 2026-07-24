"use client";

import { useRef, useState } from "react";
import { uploadWithProgress } from "@/lib/api";
import { useToast } from "./ToastProvider";

interface MediaItem {
  url: string;
  kind: "image" | "video";
}

const VIDEO_RE = /\.(mp4|mov|webm|ogg|avi|mkv|m4v)(\?|#|$)/i;

function parseItems(value: string): MediaItem[] {
  if (!value) return [];
  return value
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean)
    .map((url) => ({
      url,
      kind: VIDEO_RE.test(url) ? "video" : "image",
    }));
}

interface UploadingItem {
  name: string;
  progress: number;
}

interface MediaUploaderProps {
  value: string;
  onChange: (next: string) => void;
  max?: number;
}

// 媒体上传区：拍照 / 录像 / 相册，上传到 /api/upload，展示缩略图、上传进度与全屏预览
export function MediaUploader({ value, onChange, max = 9 }: MediaUploaderProps) {
  const photoRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLInputElement>(null);
  const albumRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();
  const [uploading, setUploading] = useState<UploadingItem[]>([]);
  const [preview, setPreview] = useState<MediaItem | null>(null);

  const items = parseItems(value);

  async function handleFiles(files: FileList | null) {
    if (!files || files.length === 0) return;
    if (items.length + uploading.length + files.length > max) {
      toast(`最多上传 ${max} 个媒体`, "error");
      return;
    }
    const uploaded: string[] = [];
    for (const file of Array.from(files)) {
      setUploading((prev) => [...prev, { name: file.name, progress: 0 }]);
      try {
        const url = await uploadWithProgress(file, (p) => {
          setUploading((prev) =>
            prev.map((u) => (u.name === file.name ? { ...u, progress: p } : u))
          );
        });
        uploaded.push(url);
      } catch (e) {
        toast(e instanceof Error ? e.message : "上传失败", "error");
      } finally {
        setUploading((prev) => prev.filter((u) => u.name !== file.name));
      }
    }
    if (uploaded.length) {
      onChange([...items.map((i) => i.url), ...uploaded].join(","));
      toast("上传成功", "success");
    }
    [photoRef, videoRef, albumRef].forEach((r) => {
      if (r.current) r.current.value = "";
    });
  }

  function remove(url: string) {
    onChange(items.filter((i) => i.url !== url).map((i) => i.url).join(","));
  }

  const actions = [
    { key: "photo", label: "拍照", icon: "📷", ref: photoRef, accept: "image/*", capture: "environment" as const },
    { key: "video", label: "录像", icon: "🎥", ref: videoRef, accept: "video/*", capture: "environment" as const },
    { key: "album", label: "相册", icon: "🖼️", ref: albumRef, accept: "image/*,video/*", capture: undefined },
  ];

  const busy = uploading.length > 0;

  return (
    <div>
      <input ref={photoRef} type="file" accept="image/*" capture="environment" className="hidden" onChange={(e) => handleFiles(e.target.files)} />
      <input ref={videoRef} type="file" accept="video/*" capture="environment" className="hidden" onChange={(e) => handleFiles(e.target.files)} />
      <input ref={albumRef} type="file" accept="image/*,video/*" multiple className="hidden" onChange={(e) => handleFiles(e.target.files)} />

      <div className="grid grid-cols-3 gap-3">
        {items.map((item) => (
          <button
            type="button"
            key={item.url}
            onClick={() => setPreview(item)}
            className="relative aspect-square rounded-xl overflow-hidden bg-gray-100 border border-gray-200 active:opacity-90"
          >
            {item.kind === "video" ? (
              <>
                {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
                <video src={item.url} className="media-thumb w-full h-full" muted playsInline />
                <span className="absolute bottom-1 right-1 w-6 h-6 rounded-full bg-black/55 text-white text-xs flex items-center justify-center">▶</span>
              </>
            ) : (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={item.url} alt="" className="media-thumb w-full h-full" />
            )}
            <span
              role="button"
              aria-label="删除"
              onClick={(e) => {
                e.stopPropagation();
                remove(item.url);
              }}
              className="absolute top-1 right-1 w-6 h-6 rounded-full bg-black/60 text-white text-sm flex items-center justify-center"
            >
              ×
            </span>
          </button>
        ))}

        {uploading.map((u) => (
          <div key={u.name} className="relative aspect-square rounded-xl overflow-hidden bg-gray-100 border border-gray-200 flex flex-col items-center justify-center">
            <div className="w-10 h-10 rounded-full flex items-center justify-center bg-emergency-blue/10 text-emergency-blue text-sm font-semibold">
              {u.progress}%
            </div>
            <span className="mt-1 text-[10px] text-gray-400 px-1 truncate w-full text-center">上传中…</span>
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-200">
              <div className="h-full bg-emergency-blue transition-all" style={{ width: `${u.progress}%` }} />
            </div>
          </div>
        ))}

        {items.length + uploading.length < max && (
          <button
            type="button"
            onClick={() => photoRef.current?.click()}
            disabled={busy}
            className="aspect-square rounded-xl border-2 border-dashed border-gray-300 text-gray-400 flex flex-col items-center justify-center gap-1 active:bg-gray-50 disabled:opacity-60"
          >
            <span className="text-2xl">＋</span>
            <span className="text-xs">{busy ? "上传中…" : "添加媒体"}</span>
          </button>
        )}
      </div>

      {/* 快捷动作：拍照 / 录像 / 相册 */}
      {items.length + uploading.length < max && (
        <div className="mt-3 grid grid-cols-3 gap-3">
          {actions.map((a) => (
            <button
              key={a.key}
              type="button"
              disabled={busy}
              onClick={() => a.ref.current?.click()}
              className="flex flex-col items-center justify-center gap-1 py-3 rounded-xl bg-white border border-gray-200 text-gray-600 active:bg-gray-50 disabled:opacity-60"
            >
              <span className="text-xl">{a.icon}</span>
              <span className="text-xs">{a.label}</span>
            </button>
          ))}
        </div>
      )}

      {/* 全屏预览 */}
      {preview && (
        <div
          className="fixed inset-0 z-[70] bg-black/90 flex items-center justify-center animate-fade-in"
          onClick={() => setPreview(null)}
        >
          <button
            aria-label="关闭"
            className="absolute top-4 right-4 w-10 h-10 rounded-full bg-white/15 text-white text-2xl flex items-center justify-center"
            onClick={() => setPreview(null)}
          >
            ×
          </button>
          {preview.kind === "video" ? (
            // eslint-disable-next-line jsx-a11y/media-has-caption
            <video src={preview.url} className="max-w-full max-h-[85vh] rounded-lg" controls autoPlay playsInline onClick={(e) => e.stopPropagation()} />
          ) : (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={preview.url} alt="" className="max-w-full max-h-[85vh] rounded-lg" onClick={(e) => e.stopPropagation()} />
          )}
        </div>
      )}
    </div>
  );
}
