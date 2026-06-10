import type { SVGProps } from "react";

type IconName =
  | "dashboard"
  | "tag"
  | "beaker"
  | "clipboard"
  | "doc"
  | "device"
  | "layers"
  | "book"
  | "logout"
  | "check"
  | "x"
  | "plus";

const PATHS: Record<IconName, string> = {
  dashboard: "M3 3h7v7H3zM14 3h7v4h-7zM14 10h7v11h-7zM3 14h7v7H3z",
  tag: "M3 12l9-9 9 9-9 9z M12 7h.01",
  beaker: "M9 3h6 M10 3v6l-5 9a2 2 0 002 3h10a2 2 0 002-3l-5-9V3",
  clipboard: "M9 4h6v3H9z M7 5H5v16h14V5h-2",
  doc: "M7 3h7l5 5v13H7z M14 3v5h5",
  device: "M8 3h8v18H8z M11 18h2",
  layers: "M12 3l9 5-9 5-9-5 9-5z M3 13l9 5 9-5 M3 17l9 5 9-5",
  book: "M4 5a2 2 0 012-2h12v16H6a2 2 0 00-2 2z M18 17H6a2 2 0 00-2 2",
  logout: "M15 12H4 M9 7l-5 5 5 5 M15 4h5v16h-5",
  check: "M5 13l4 4L19 7",
  x: "M6 6l12 12 M18 6L6 18",
  plus: "M12 5v14 M5 12h14",
};

export function Icon({
  name,
  ...props
}: { name: IconName } & SVGProps<SVGSVGElement>) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
      width={20}
      height={20}
      aria-hidden="true"
      {...props}
    >
      <path d={PATHS[name]} />
    </svg>
  );
}

export type { IconName };
