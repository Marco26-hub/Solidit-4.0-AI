import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui";

/**
 * Photo input that offers BOTH a file picker (with mobile camera capture) and a
 * live webcam capture (getUserMedia). On capture it produces a JPEG File and
 * calls onFile. Secure-context only (localhost or https) for the webcam.
 */
export function PhotoInput({
  onFile,
  accept = "image/*",
}: {
  onFile: (file: File | null) => void;
  accept?: string;
}) {
  const [streaming, setStreaming] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [name, setName] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const stopStream = () => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    setStreaming(false);
  };

  useEffect(() => () => stopStream(), []);

  const accept_set = (file: File | null) => {
    onFile(file);
    setName(file ? file.name : null);
    setPreviewUrl((old) => {
      if (old) URL.revokeObjectURL(old);
      return file ? URL.createObjectURL(file) : null;
    });
  };

  async function openCamera() {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: "environment" } },
        audio: false,
      });
      streamRef.current = stream;
      setStreaming(true);
      // assign after render
      setTimeout(() => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          videoRef.current.play().catch((e) => console.warn("PhotoInput: video play failed", e));
        }
      }, 0);
    } catch (e) {
      setError(
        "Fotocamera non disponibile (serve permesso + contesto sicuro https/localhost). Usa 'Scegli file'."
      );
      stopStream();
    }
  }

  function shoot() {
    const v = videoRef.current;
    if (!v) return;
    const canvas = document.createElement("canvas");
    canvas.width = v.videoWidth || 1280;
    canvas.height = v.videoHeight || 720;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.drawImage(v, 0, 0, canvas.width, canvas.height);
    canvas.toBlob(
      (blob) => {
        if (blob) {
          const file = new File([blob], `capture-${canvas.width}x${canvas.height}.jpg`, {
            type: "image/jpeg",
          });
          accept_set(file);
        }
        stopStream();
      },
      "image/jpeg",
      0.92
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center gap-2">
        <label className="cursor-pointer rounded-lg border border-slate-200 px-3 py-2 text-sm text-steel hover:bg-slate-50 min-h-[40px] inline-flex items-center">
          Scegli file
          <input
            type="file"
            accept={accept}
            capture="environment"
            className="hidden"
            onChange={(e) => accept_set(e.target.files?.[0] ?? null)}
          />
        </label>
        {!streaming ? (
          <Button type="button" variant="ghost" onClick={openCamera}>
            📷 Fotocamera
          </Button>
        ) : (
          <>
            <Button type="button" onClick={shoot}>
              Scatta
            </Button>
            <Button type="button" variant="ghost" onClick={stopStream}>
              Annulla
            </Button>
          </>
        )}
        {name && !streaming && <span className="text-xs text-steel">{name}</span>}
      </div>

      {streaming && (
        <video
          ref={videoRef}
          playsInline
          muted
          className="w-full max-w-sm rounded-lg border border-slate-200 bg-black"
        />
      )}

      {previewUrl && !streaming && (
        <img
          src={previewUrl}
          alt="anteprima"
          className="w-full max-w-[200px] rounded-lg border border-slate-200"
        />
      )}

      {error && <p className="text-xs text-amber-600">{error}</p>}
    </div>
  );
}
