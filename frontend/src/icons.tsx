import type { SVGProps } from "react";

type Props = SVGProps<SVGSVGElement>;
const base = { width: 18, height: 18, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };

export const SparkIcon = (props: Props) => <svg {...base} {...props}><path d="m12 3 1.2 4.1A5 5 0 0 0 16.9 11L21 12l-4.1 1.2a5 5 0 0 0-3.7 3.7L12 21l-1.2-4.1a5 5 0 0 0-3.7-3.7L3 12l4.1-1.2a5 5 0 0 0 3.7-3.7L12 3Z" /></svg>;
export const FileIcon = (props: Props) => <svg {...base} {...props}><path d="M6 2h8l4 4v16H6z"/><path d="M14 2v5h5"/></svg>;
export const CodeIcon = (props: Props) => <svg {...base} {...props}><path d="m8 9-3 3 3 3M16 9l3 3-3 3M14 5l-4 14"/></svg>;
export const LayersIcon = (props: Props) => <svg {...base} {...props}><path d="m12 2 9 5-9 5-9-5z"/><path d="m3 12 9 5 9-5M3 17l9 5 9-5"/></svg>;
export const JiraIcon = (props: Props) => <svg {...base} {...props}><path d="M12 2 4 10l8 8 8-8z"/><path d="m8 14-4 4 4 4 4-4M16 14l4 4-4 4-4-4"/></svg>;
export const CheckIcon = (props: Props) => <svg {...base} {...props}><path d="m5 12 4 4L19 6"/></svg>;
export const ArrowIcon = (props: Props) => <svg {...base} {...props}><path d="M5 12h14M13 6l6 6-6 6"/></svg>;
export const GitIcon = (props: Props) => <svg {...base} {...props}><circle cx="6" cy="5" r="2"/><circle cx="18" cy="6" r="2"/><circle cx="6" cy="19" r="2"/><path d="M6 7v10M8 6h5a5 5 0 0 1 5 5v-3"/></svg>;
export const SearchIcon = (props: Props) => <svg {...base} {...props}><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></svg>;
export const FolderIcon = (props: Props) => <svg {...base} {...props}><path d="M3 6h7l2 2h9v11H3z"/></svg>;

