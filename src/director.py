import os
from dotenv import load_dotenv
from openai import OpenAI
from src.schemas import Storyboard, PedagogicalStoryboard
from src.config import GEMINI_BASE_URL, GEMINI_API_KEY, GEMINI_MODEL

load_dotenv()

class DirectorAgent:
    def __init__(self, api_key: str | None = None):
        self.client = OpenAI(
            api_key=api_key or GEMINI_API_KEY or os.getenv("OPENAI_API_KEY"),
            base_url=GEMINI_BASE_URL,
        )

    def create_storyboard(self, document_text: str, beat_count: int = 5) -> Storyboard:
        """
        Transforms arbitrary technical/academic document content into a structured,
        topic-agnostic pedagogical video storyboard using a lightweight, unified schema.
        """
        prompt = f"""
You are an elite professor and lead educator combining the academic depth of MIT OpenCourseWare with the visual clarity of Fireship.
Analyze the following document text and transform it into a masterclass educational video script of EXACTLY {beat_count} sequential beats.

TOPIC-AGNOSTIC EXTRACTION RULE:
Adapt all concepts, badges, code, and cards directly to the specific subject matter in the text:
- Machine Learning / AI: neural architectures, tensors, loss functions, PyTorch/Python snippets, training pipelines.
- Cloud / Distributed Systems: microservices, load balancing, containers, Kubernetes, bash/yaml.
- Biology / Medicine: genetics, cell biology, enzymes, molecular pathways, pseudocode/models.
- Finance / Business: market dynamics, asset valuation, risk modeling, accounting ledgers.
- General Science / Engineering: physical systems, math equations, workflows, and exact terms from the document.
NEVER default to SQL or databases unless the document explicitly discusses SQL/databases!

Two-Part Narration Formula:
For every beat, `narration` MUST follow this exact two-part pedagogical structure:
1. FIRST, read the on-screen title and the bullet points clearly so the viewer immediately connects what they hear with what they see.
2. THEN, transition directly into a teacher-style explanation breaking down the concept with intuitive reasoning, why it matters, and a real-world parallel.

Visual Cards (`visual_cards`) per `visual_type`:
1. When `visual_type == 'comparison_matrix'`:
   - Generate EXACTLY 4 `visual_cards` with distinct concepts and accent colors:
     * Card 1: accent_color='cyan'
     * Card 2: accent_color='emerald'
     * Card 3: accent_color='amber'
     * Card 4: accent_color='rose'
   - Each card must have a contextual 1-2 word `badge`, a clear `title`, and a 4-8 word `description`.
   - `code_snippet` should be an empty string "".
2. When `visual_type == 'pipeline_flow'`:
   - Generate EXACTLY 3 sequential `visual_cards`:
     * Card 1: badge='01', title='Stage 1 Name', description='Stage 1 explanation', accent_color='cyan'
     * Card 2: badge='02', title='Stage 2 Name', description='Stage 2 explanation', accent_color='blue'
     * Card 3: badge='03', title='Stage 3 Name', description='Stage 3 explanation', accent_color='purple'
   - `code_snippet` should be an empty string "".
3. When `visual_type == 'metaphor_illustration'`:
   - Generate EXACTLY 2 `visual_cards`:
     * Card 1: badge='ANALOGY', title='Real-World Metaphor', description='Intuitive real-world comparison quote or mental model', accent_color='amber'
     * Card 2: badge='TECH REALITY', title='System Reality', description='How the real technical mechanism functions in practice', accent_color='cyan'
   - `code_snippet` should be an empty string "".
4. When `visual_type == 'code_window'`:
   - `visual_cards` MUST be an empty list [].
   - Provide 3-6 lines of clean, authentic formatted code in `code_snippet`.
   - Set `code_language` to the appropriate language ('python', 'javascript', 'bash', 'sql', 'pseudocode').

Story Arc ({beat_count} Beats):
- Beat 1: Core Problem & Intuitive Mental Model (`visual_type`: "metaphor_illustration", mascot: "thinking" or "shrugging")
- Beat 2: Structural Pipeline & Workflow (`visual_type`: "pipeline_flow", mascot: "explaining")
- Beat 3: Key Components & Comparative Analysis (`visual_type`: "comparison_matrix", mascot: "pointing_stick")
- Beat 4: Concrete Implementation / Mechanics (`visual_type`: "code_window", mascot: "pointing_stick")
- Beat 5+: Synthesis, Trade-offs & Production Impact (`visual_type`: "metaphor_illustration" or "comparison_matrix", mascot: "arms_crossed")

Field Specifications:
- `beat_id`: int (Sequential beat index starting at 1)
- `category_badge`: str (Short topic badge from the document)
- `title`: str (Clean, bold heading, 3-6 words)
- `on_screen_points`: List[str] (Exactly 2 to 3 concise, impactful bullet points for the left column)
- `caption_pill`: str (3-5 uppercase words for the bottom floating pill)
- `visual_title`: str (Header for the right visual card)
- `visual_type`: Literal["comparison_matrix", "pipeline_flow", "code_window", "metaphor_illustration"]
- `mascot_pose`: Literal["pointing_stick", "thinking", "explaining", "shrugging", "arms_crossed"]
- `visual_cards`: List[VisualCard] (Populated according to visual_type rules above)
- `code_snippet`: str (Code snippet for code_window, else empty string)
- `code_language`: str (Language for code_snippet, default 'python')
- `narration`: str (Two-part teacher narration formula)

Document Text:
{document_text[:6500]}
"""

        completion = self.client.beta.chat.completions.parse(
            model=GEMINI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a world-class educational director producing high-retention video scripts. "
                        "You adapt completely to any document topic (AI, Systems, Science, Economics, etc.). "
                        "You strictly enforce the two-part pedagogical narration formula and populate "
                        "the visual_cards and code_snippet fields according to the visual_type specification."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            response_format=Storyboard,
        )
        return completion.choices[0].message.parsed