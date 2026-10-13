from pydantic import BaseModel, Field
from typing import List, Literal

MascotPose = Literal["pointing_stick", "thinking", "explaining", "shrugging", "arms_crossed"]
VisualType = Literal["comparison_matrix", "pipeline_flow", "code_window", "metaphor_illustration"]

class VisualCard(BaseModel):
    badge: str = Field(description="1-2 word contextual tag, e.g. 'INPUT', 'STEP 01', 'ANALOGY', 'LAYER 1'")
    title: str = Field(description="Component or concept name")
    description: str = Field(description="Concise 4-8 word explanation")
    accent_color: str = Field(default="cyan", description="Color name: cyan, emerald, amber, rose, blue, or purple")

class Beat(BaseModel):
    beat_id: int
    category_badge: str = Field(description="Short topic badge from the document")
    title: str = Field(description="On-screen headline, 3-6 words")
    on_screen_points: List[str] = Field(description="2-3 concise bullet points for the left column", max_length=3)
    caption_pill: str = Field(description="3-5 uppercase words for bottom pill")
    visual_title: str = Field(description="Header for the right visual card")
    visual_type: Literal["comparison_matrix", "pipeline_flow", "code_window", "metaphor_illustration"]
    mascot_pose: Literal["pointing_stick", "thinking", "explaining", "shrugging", "arms_crossed"]
    visual_cards: List[VisualCard] = Field(
        default_factory=list,
        description="Cards to display: 4 items for comparison_matrix, 3 items for pipeline_flow, 2 items for metaphor_illustration, empty for code_window"
    )
    code_snippet: str = Field(default="", description="Clean formatted code snippet if visual_type == 'code_window', else empty string")
    code_language: str = Field(default="python", description="Language for code snippet: python, javascript, sql, bash, or pseudocode")
    narration: str = Field(description="Two-part teacher narration: first reads on-screen title and points verbatim, then explains intuition and analogies")

    # Backward compatibility properties
    @property
    def diagram_title(self) -> str:
        return self.visual_title or self.title

    @property
    def analogy_hint(self) -> str:
        return self.category_badge

    @property
    def metaphor_text(self) -> str:
        return self.visual_title

    @property
    def diagram_nodes(self) -> List[str]:
        if self.visual_cards:
            return [c.title for c in self.visual_cards]
        return self.on_screen_points

class Storyboard(BaseModel):
    project_title: str
    topic_analogy: str = Field(default="", description="Overarching real-world analogy framing the technical topic")
    beats: List[Beat]

PedagogicalStoryboard = Storyboard