export interface Message {
  id: string;
  sender: "user" | "bot";
  text: string;
  timestamp: string;
  quickReplies?: Array<{
    label: string;
    value: string;
  }>;
  helpAssessment?: {
    canHelp: "yes" | "maybe";
    reason: string;
    matchedSkills?: string[];
    suggestedAlternativeSkills?: string[];
  };
}
