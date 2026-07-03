import { type LucideIcon } from "lucide-react";

interface IconProps {
  icon: LucideIcon;
  className?: string;
  size?: number;
}

export default function Icon({ icon: LucideIcon, className = "", size = 18 }: IconProps) {
  return <LucideIcon className={className} size={size} />;
}
