export interface Source {
  url: string;
  favicon: string; // this is a url to the icon
}

export interface CheckedFact {
  text: string;
  truthfulness: "SOMEWHAT TRUE" | "FALSE" | "TRUE";
  summary: string;
  sources: Source[];
}

export type TruthfulnessType = CheckedFact["truthfulness"];
