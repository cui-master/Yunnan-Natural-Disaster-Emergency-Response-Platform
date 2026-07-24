// 灾害类型枚举（type 取值，必须与服务端一致）
export interface DisasterTypeOption {
  value: string;
  label: string;
  icon: string;
  badge: string; // tailwind 颜色类
}

export const DISASTER_TYPES: DisasterTypeOption[] = [
  { value: "EARTHQUAKE", label: "地震", icon: "🌐", badge: "bg-orange-100 text-orange-700" },
  { value: "FLOOD", label: "洪涝", icon: "🌊", badge: "bg-blue-100 text-blue-700" },
  { value: "LANDSLIDE", label: "滑坡", icon: "⛰️", badge: "bg-amber-100 text-amber-700" },
  { value: "DEBRIS_FLOW", label: "泥石流", icon: "🪨", badge: "bg-yellow-100 text-yellow-800" },
  { value: "DROUGHT", label: "干旱", icon: "☀️", badge: "bg-red-100 text-red-700" },
  { value: "FOREST_FIRE", label: "森林火灾", icon: "🔥", badge: "bg-red-100 text-red-800" },
  { value: "HAIL", label: "冰雹", icon: "🌨️", badge: "bg-cyan-100 text-cyan-700" },
  { value: "TYPHOON", label: "台风", icon: "🌀", badge: "bg-indigo-100 text-indigo-700" },
];

// 等级枚举（level 取值）
export interface LevelOption {
  value: string;
  label: string; // 中文含义
  roman: string; // 罗马数字
  badge: string;
}

export const LEVELS: LevelOption[] = [
  { value: "I", label: "特别重大", roman: "Ⅰ级", badge: "bg-red-600 text-white" },
  { value: "II", label: "重大", roman: "Ⅱ级", badge: "bg-orange-500 text-white" },
  { value: "III", label: "较大", roman: "Ⅲ级", badge: "bg-amber-500 text-white" },
  { value: "IV", label: "一般", roman: "Ⅳ级", badge: "bg-blue-500 text-white" },
];

// 状态枚举（status 取值）
export interface StatusOption {
  label: string;
  badge: string;
}

export const STATUS_MAP: Record<string, StatusOption> = {
  PENDING_VERIFY: { label: "待核验", badge: "bg-amber-100 text-amber-700" },
  CONFIRMED: { label: "已确认", badge: "bg-blue-100 text-blue-700" },
  IN_PROGRESS: { label: "处置中", badge: "bg-indigo-100 text-indigo-700" },
  CLOSED: { label: "已结束", badge: "bg-gray-200 text-gray-600" },
  REJECTED: { label: "已驳回", badge: "bg-red-100 text-red-700" },
};

export function getDisasterType(value: string): DisasterTypeOption | undefined {
  return DISASTER_TYPES.find((t) => t.value === value);
}

export function getLevel(value: string): LevelOption | undefined {
  return LEVELS.find((l) => l.value === value);
}

export function getStatus(value?: string): StatusOption {
  if (!value) return { label: "未知", badge: "bg-gray-100 text-gray-500" };
  return STATUS_MAP[value] ?? { label: value, badge: "bg-gray-100 text-gray-500" };
}

// 演示账号
export const DEMO_ACCOUNT = { username: "reporter", password: "123456" };
