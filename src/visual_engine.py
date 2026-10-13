import asyncio
import base64
import io
from pathlib import Path
from typing import List, Union, Dict, Any, Optional
from PIL import Image
from playwright.async_api import async_playwright
from src.schemas import Beat, VisualCard

THEME_COLOR_STYLES: Dict[str, Dict[str, str]] = {
    "cyan": {
        "border": "border-cyan-400/80",
        "bg": "bg-cyan-950/50",
        "badge_bg": "bg-cyan-500/20",
        "badge_text": "text-cyan-300",
        "badge_border": "border-cyan-400/40",
        "accent": "text-cyan-400",
        "glow": "shadow-[0_0_20px_rgba(34,211,238,0.18)]",
    },
    "emerald": {
        "border": "border-emerald-400/80",
        "bg": "bg-emerald-950/50",
        "badge_bg": "bg-emerald-500/20",
        "badge_text": "text-emerald-300",
        "badge_border": "border-emerald-400/40",
        "accent": "text-emerald-400",
        "glow": "shadow-[0_0_20px_rgba(16,185,129,0.18)]",
    },
    "amber": {
        "border": "border-amber-400/80",
        "bg": "bg-amber-950/50",
        "badge_bg": "bg-amber-500/20",
        "badge_text": "text-amber-300",
        "badge_border": "border-amber-400/40",
        "accent": "text-amber-400",
        "glow": "shadow-[0_0_20px_rgba(245,158,11,0.18)]",
    },
    "rose": {
        "border": "border-rose-400/80",
        "bg": "bg-rose-950/50",
        "badge_bg": "bg-rose-500/20",
        "badge_text": "text-rose-300",
        "badge_border": "border-rose-400/40",
        "accent": "text-rose-400",
        "glow": "shadow-[0_0_20px_rgba(244,63,94,0.18)]",
    },
    "purple": {
        "border": "border-purple-400/80",
        "bg": "bg-purple-950/50",
        "badge_bg": "bg-purple-500/20",
        "badge_text": "text-purple-300",
        "badge_border": "border-purple-400/40",
        "accent": "text-purple-400",
        "glow": "shadow-[0_0_20px_rgba(168,85,247,0.18)]",
    },
    "blue": {
        "border": "border-blue-400/80",
        "bg": "bg-blue-950/50",
        "badge_bg": "bg-blue-500/20",
        "badge_text": "text-blue-300",
        "badge_border": "border-blue-400/40",
        "accent": "text-blue-400",
        "glow": "shadow-[0_0_20px_rgba(59,130,246,0.18)]",
    },
}

def get_style(color_name: str) -> Dict[str, str]:
    c = (color_name or "cyan").lower().strip()
    return THEME_COLOR_STYLES.get(c, THEME_COLOR_STYLES["cyan"])

class VisualEngine:
    @staticmethod
    def _get_mascot_base64(pose: str) -> str:
        """Resolves mascot image from assets/mascot/{pose}.png or assets/{pose}.png into base64 URI with transparent margin cropping."""
        possible_paths = [
            Path(f"assets/mascot/{pose}.png"),
            Path(f"assets/{pose}.png"),
            Path(f"data/assets/{pose}.png"),
        ]
        for p in possible_paths:
            if p.is_file():
                try:
                    im = Image.open(p)
                    bbox = im.getbbox()
                    if bbox:
                        im = im.crop(bbox)
                    buf = io.BytesIO()
                    im.save(buf, format="PNG")
                    encoded = base64.b64encode(buf.getvalue()).decode("utf-8")
                    return f"data:image/png;base64,{encoded}"
                except Exception:
                    encoded = base64.b64encode(p.read_bytes()).decode("utf-8")
                    return f"data:image/png;base64,{encoded}"
        return ""

    @staticmethod
    def _format_point_card(point: str) -> str:
        """Formats an on-screen bullet point into a high-contrast card with bold title/accent word."""
        if ":" in point:
            parts = point.split(":", 1)
            title = parts[0].strip()
            desc = parts[1].strip()
        elif " - " in point:
            parts = point.split(" - ", 1)
            title = parts[0].strip()
            desc = parts[1].strip()
        else:
            words = point.split()
            if len(words) >= 4:
                title = " ".join(words[:2])
                desc = " ".join(words[2:])
            else:
                title = point
                desc = ""

        desc_html = f'<p class="text-xl text-slate-100 leading-snug pl-6">{desc}</p>' if desc else ""

        return f"""
        <div class="p-5 rounded-2xl bg-slate-900/80 border border-slate-700/80 shadow-xl space-y-2 backdrop-blur-md">
            <div class="flex items-center space-x-3">
                <span class="w-3 h-3 rounded-full bg-cyan-400 shadow-[0_0_10px_rgba(34,211,238,0.8)] shrink-0"></span>
                <span class="text-xl font-extrabold text-cyan-300 tracking-wide">{title}</span>
            </div>
            {desc_html}
        </div>
        """

    @classmethod
    def _render_comparison_matrix(cls, beat: Beat, mascot_b64: str) -> str:
        """Renders dynamic 2x2 comparison matrix from beat.visual_cards."""
        cards = beat.visual_cards or []
        fallback_colors = ["cyan", "emerald", "amber", "rose"]

        if len(cards) < 4:
            nodes = beat.on_screen_points + [beat.title, beat.caption_pill]
            cards = []
            for i in range(4):
                node_text = nodes[i % len(nodes)]
                color = fallback_colors[i % len(fallback_colors)]
                cards.append(
                    VisualCard(
                        badge=f"ITEM 0{i+1}",
                        title=node_text[:28],
                        description=f"Core facet of {beat.visual_title[:20]}",
                        accent_color=color,
                    )
                )

        cards_html = ""
        for item in cards[:4]:
            styles = get_style(item.accent_color)
            cards_html += f"""
            <div class="border-2 {styles['border']} {styles['bg']} rounded-2xl p-4 min-h-[145px] flex flex-col justify-between {styles['glow']}">
                <div class="flex items-center justify-between">
                    <span class="text-xs font-mono font-black uppercase tracking-wider px-2.5 py-1 rounded-full {styles['badge_bg']} {styles['badge_text']} border {styles['badge_border']}">
                        {item.badge}
                    </span>
                    <span class="text-[11px] font-mono {styles['accent']} font-semibold">● Active</span>
                </div>
                <p class="text-base font-extrabold text-slate-50 leading-snug line-clamp-2 my-1">{item.title}</p>
                <div class="text-[11px] font-mono {styles['accent']} leading-tight line-clamp-1">{item.description}</div>
            </div>
            """

        return f"""
        <div class="flex-1 flex flex-col justify-between w-full h-full relative z-10 pt-1">
            <!-- Dynamic 2x2 Matrix Cards -->
            <div class="grid grid-cols-2 gap-3.5 w-full">
                {cards_html}
            </div>

            <!-- Mascot Stage below 2x2 Matrix -->
            <div class="flex justify-center items-end relative -mb-6 mt-1">
                <div class="absolute bottom-0 w-[260px] h-[300px] bg-cyan-500/15 rounded-full blur-[60px] pointer-events-none"></div>
                <div class="max-h-[360px] flex items-end">
                    <img src="{mascot_b64}" class="max-h-[360px] w-auto max-w-full object-contain object-bottom drop-shadow-[0_20px_35px_rgba(0,0,0,0.8)] select-none" alt="Mascot" />
                </div>
            </div>
        </div>
        """

    @classmethod
    def _render_pipeline_flow(cls, beat: Beat, mascot_b64: str) -> str:
        """Renders dynamic 3-step vertical pipeline flow from beat.visual_cards with arrow connectors."""
        cards = beat.visual_cards or []
        if len(cards) < 3:
            nodes = beat.on_screen_points + [beat.title]
            colors = ["cyan", "blue", "purple"]
            cards = [
                VisualCard(
                    badge=f"0{i+1}",
                    title=nodes[i % len(nodes)][:30],
                    description=f"Phase {i+1} transformation in pipeline",
                    accent_color=colors[i % len(colors)],
                )
                for i in range(3)
            ]

        steps_html = ""
        for idx, step in enumerate(cards[:3]):
            step_tag = step.badge if step.badge else f"0{idx+1}"
            styles = get_style(step.accent_color)
            connector = ""
            if idx < 2:
                connector = """
                <div class="flex justify-center my-1 text-cyan-400 animate-pulse">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 14l-7 7m0 0l-7-7m7 7V3"></path>
                    </svg>
                </div>
                """

            steps_html += f"""
            <div class="border-2 {styles['border']} bg-gradient-to-r from-blue-950/80 to-slate-900/95 rounded-2xl p-3.5 flex items-center space-x-3.5 {styles['glow']}">
                <div class="w-11 h-11 rounded-xl {styles['badge_bg']} border {styles['badge_border']} flex items-center justify-center font-black text-base {styles['badge_text']} shrink-0">
                    {step_tag}
                </div>
                <div class="flex-1 min-w-0">
                    <div class="flex items-center justify-between">
                        <span class="text-[10px] uppercase font-mono {styles['accent']} font-bold tracking-wider">STAGE {step_tag}</span>
                    </div>
                    <p class="text-sm font-bold text-slate-50 leading-snug truncate">{step.title}</p>
                    <p class="text-[11px] text-slate-400 leading-tight truncate">{step.description}</p>
                </div>
            </div>
            {connector}
            """

        return f"""
        <div class="flex-1 flex items-center justify-between w-full h-full relative z-10 py-1">
            <!-- 3-Node Vertical Pipeline -->
            <div class="flex-1 max-w-[340px] space-y-1.5">
                {steps_html}
            </div>

            <!-- Mascot Stage Alongside Pipeline -->
            <div class="flex-1 flex justify-center items-end h-full relative">
                <div class="absolute bottom-4 w-[240px] h-[360px] bg-cyan-500/15 rounded-full blur-[60px] pointer-events-none"></div>
                <div class="max-h-[500px] flex items-end">
                    <img src="{mascot_b64}" class="max-h-[500px] w-auto max-w-full object-contain object-bottom drop-shadow-[0_20px_35px_rgba(0,0,0,0.8)] select-none" alt="Mascot" />
                </div>
            </div>
        </div>
        """

    @classmethod
    def _render_code_window(cls, beat: Beat, mascot_b64: str) -> str:
        """Renders dark macOS-style terminal using beat.code_snippet and beat.code_language."""
        lang = (beat.code_language or "python").lower().strip()
        ext_map = {
            "python": "py",
            "javascript": "js",
            "typescript": "ts",
            "bash": "sh",
            "sql": "sql",
            "pseudocode": "txt",
        }
        ext = ext_map.get(lang, "py")
        filename = f"pipeline.{ext}"
        code_text = beat.code_snippet if beat.code_snippet else "# Core execution routine\nmodel = init_engine()\noutput = model.run(data)\nprint('Done.')"

        code_lines = [l for l in code_text.strip().split("\n") if l.strip() or len(code_text.splitlines()) <= 5]
        formatted_code = "<br/>".join(
            f'<span class="text-slate-500 font-mono text-xs select-none mr-3">{i+1:02d}</span><span class="text-cyan-300 font-semibold text-sm">{line}</span>'
            for i, line in enumerate(code_lines[:6])
        )

        return f"""
        <div class="flex-1 flex flex-col justify-between w-full h-full relative z-10 pt-1">
            <!-- Dark macOS Code Terminal -->
            <div class="bg-[#030712] border-2 border-cyan-500/50 rounded-2xl shadow-[0_0_30px_rgba(34,211,238,0.2)] overflow-hidden w-full">
                <!-- macOS Title Bar -->
                <div class="bg-slate-900/95 border-b border-slate-800 px-4 py-2.5 flex items-center justify-between">
                    <div class="flex items-center space-x-2">
                        <span class="w-3 h-3 rounded-full bg-red-500"></span>
                        <span class="w-3 h-3 rounded-full bg-yellow-500"></span>
                        <span class="w-3 h-3 rounded-full bg-green-500"></span>
                    </div>
                    <span class="text-xs font-mono text-slate-300 font-bold tracking-wider">{filename}</span>
                    <span class="text-xs font-mono text-emerald-400 uppercase font-semibold">● {lang.upper()}</span>
                </div>
                <!-- Monospaced Code View -->
                <div class="p-4 font-mono leading-relaxed bg-[#060a17]/95 overflow-hidden">
                    {formatted_code}
                </div>
                <!-- Dynamic Execution Status Bar -->
                <div class="bg-slate-950 border-t border-slate-800/90 px-4 py-2.5 flex items-center justify-between text-xs font-mono">
                    <span class="text-slate-400">STATUS:</span>
                    <span class="text-cyan-300 font-bold">{beat.caption_pill}</span>
                </div>
            </div>

            <!-- Mascot Stage below Code Terminal -->
            <div class="flex justify-center items-end relative -mb-6 mt-1">
                <div class="absolute bottom-0 w-[260px] h-[320px] bg-cyan-500/15 rounded-full blur-[60px] pointer-events-none"></div>
                <div class="max-h-[350px] flex items-end">
                    <img src="{mascot_b64}" class="max-h-[350px] w-auto max-w-full object-contain object-bottom drop-shadow-[0_20px_35px_rgba(0,0,0,0.8)] select-none" alt="Mascot" />
                </div>
            </div>
        </div>
        """

    @classmethod
    def _render_metaphor_illustration(cls, beat: Beat, mascot_b64: str) -> str:
        """Renders 2 comparison blocks from beat.visual_cards."""
        cards = beat.visual_cards or []
        if len(cards) < 2:
            card_0 = VisualCard(
                badge="ANALOGY",
                title="Real-World Metaphor",
                description=beat.visual_title or f"Intuitive mental model for {beat.title}",
                accent_color="amber"
            )
            card_1 = VisualCard(
                badge="TECH REALITY",
                title="System Mechanism",
                description=beat.on_screen_points[0] if beat.on_screen_points else "Concrete operational flow",
                accent_color="cyan"
            )
            cards = [card_0, card_1]

        c0 = cards[0]
        c1 = cards[1]
        s0 = get_style(c0.accent_color or "amber")
        s1 = get_style(c1.accent_color or "cyan")

        return f"""
        <div class="flex-1 flex items-center justify-between w-full h-full relative z-10 py-1">
            <!-- Illustrated Comparison Blocks -->
            <div class="flex-1 max-w-[340px] space-y-3.5">
                <!-- Card 1 (Analogy) -->
                <div class="border-2 {s0['border']} {s0['bg']} rounded-2xl p-5 min-h-[200px] {s0['glow']} flex flex-col justify-between">
                    <div>
                        <span class="px-2.5 py-1 rounded-full {s0['badge_bg']} {s0['badge_text']} border {s0['badge_border']} text-[11px] font-mono font-bold uppercase tracking-wider">
                            💡 {c0.badge}
                        </span>
                    </div>
                    <div>
                        <div class="text-sm font-bold text-slate-300">{c0.title}</div>
                        <p class="text-base font-extrabold text-slate-50 italic leading-relaxed my-1.5">
                            “{c0.description}”
                        </p>
                    </div>
                    <div class="text-[10px] font-mono {s0['accent']} uppercase tracking-widest font-semibold">
                        ● Intuitive Model
                    </div>
                </div>

                <!-- Card 2 (Technical Reality) -->
                <div class="border-2 {s1['border']} {s1['bg']} rounded-2xl p-5 min-h-[200px] {s1['glow']} flex flex-col justify-between">
                    <div>
                        <span class="px-2.5 py-1 rounded-full {s1['badge_bg']} {s1['badge_text']} border {s1['badge_border']} text-[11px] font-mono font-bold uppercase tracking-wider">
                            ⚙️ {c1.badge}
                        </span>
                    </div>
                    <div>
                        <div class="text-sm font-bold text-slate-300">{c1.title}</div>
                        <p class="text-sm font-semibold text-slate-100 leading-relaxed my-1.5">
                            {c1.description}
                        </p>
                    </div>
                    <div class="text-[10px] font-mono {s1['accent']} uppercase tracking-widest font-semibold">
                        ● Operational Flow
                    </div>
                </div>
            </div>

            <!-- Mascot Stage Alongside Cards -->
            <div class="flex-1 flex justify-center items-end h-full relative">
                <div class="absolute bottom-4 w-[240px] h-[360px] bg-amber-500/15 rounded-full blur-[60px] pointer-events-none"></div>
                <div class="max-h-[500px] flex items-end">
                    <img src="{mascot_b64}" class="max-h-[500px] w-auto max-w-full object-contain object-bottom drop-shadow-[0_20px_35px_rgba(0,0,0,0.8)] select-none" alt="Mascot" />
                </div>
            </div>
        </div>
        """

    @classmethod
    def _generate_right_visual_html(cls, beat: Beat, mascot_b64: str) -> str:
        """Dispatches to the appropriate dynamic visual archetype renderer based on beat.visual_type."""
        vtype = beat.visual_type

        if vtype == "comparison_matrix":
            return cls._render_comparison_matrix(beat, mascot_b64)
        elif vtype == "pipeline_flow":
            return cls._render_pipeline_flow(beat, mascot_b64)
        elif vtype == "code_window":
            return cls._render_code_window(beat, mascot_b64)
        else:  # metaphor_illustration
            return cls._render_metaphor_illustration(beat, mascot_b64)

    @classmethod
    def _build_beat_page_html(cls, beat: Beat) -> str:
        """Constructs full 1920x1080 HTML page with Content on the Left (55%) and Visual on the Right (45%)."""
        mascot_b64 = cls._get_mascot_base64(beat.mascot_pose)
        right_visual_content = cls._generate_right_visual_html(beat, mascot_b64)
        category_badge = getattr(beat, "category_badge", "CORE CONCEPT")
        beat_title = getattr(beat, "title", "Core Architecture")
        visual_title = getattr(beat, "visual_title", "System Overview")
        on_screen_points = getattr(beat, "on_screen_points", []) or ["Core concept summary", "Primary operational rule"]

        points_html = "".join(cls._format_point_card(point) for point in on_screen_points)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&display=swap');
    body {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      width: 1920px;
      height: 1080px;
      overflow: hidden;
      margin: 0;
      padding: 0;
    }}
  </style>
</head>
<body class="bg-[#060913] text-white w-[1920px] h-[1080px] overflow-hidden select-none relative box-border m-0 p-0 flex items-center justify-center">
  <!-- Subtle Ambient Glow Orbs -->
  <div class="absolute -top-32 -left-32 w-[700px] h-[700px] bg-blue-600/10 rounded-full blur-[140px] pointer-events-none"></div>
  <div class="absolute -bottom-32 -right-32 w-[700px] h-[700px] bg-cyan-600/10 rounded-full blur-[140px] pointer-events-none"></div>
  <div class="absolute top-1/2 left-1/3 -translate-y-1/2 w-[500px] h-[500px] bg-indigo-600/10 rounded-full blur-[160px] pointer-events-none"></div>

  <!-- Strict 2-Column CSS Grid: 1920x1080, p-20, items-center (Left: col-span-7, Right: col-span-5) -->
  <div class="grid grid-cols-12 gap-12 w-full h-full p-20 items-center box-border relative z-10">

    <!-- LEFT COLUMN (col-span-7, 55% width - "The Content Stage") -->
    <div class="col-span-7 flex flex-col justify-center space-y-6 h-full relative z-10">
      
      <!-- Top Category Tag: Sleek pill -->
      <div>
        <div class="inline-flex items-center space-x-2.5 px-4 py-1.5 rounded-full bg-cyan-500/15 border border-cyan-400/30 text-cyan-300 font-mono font-bold text-xs uppercase tracking-widest backdrop-blur-md shadow-sm">
          <span class="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
          <span>{category_badge} • BEAT 0{beat.beat_id}</span>
        </div>
      </div>

      <!-- Main Heading -->
      <h1 class="text-5xl font-black text-white tracking-tight leading-tight">
        {beat_title}
      </h1>

      <!-- Gradient Accent Divider -->
      <div class="w-20 h-1.5 bg-gradient-to-r from-cyan-400 to-blue-500 rounded-full"></div>

      <!-- On-Screen Points: 2-3 prominent cards -->
      <div class="space-y-4 pt-1">
        {points_html}
      </div>

      <!-- Bottom Floating Pill: A centered dark-cyan pill showing beat.caption_pill -->
      <div class="pt-3 flex justify-center">
        <div class="bg-slate-950/95 border-2 border-cyan-400/90 px-8 py-3 rounded-full shadow-[0_0_30px_rgba(34,211,238,0.35)] inline-flex items-center space-x-3.5 backdrop-blur-md">
          <span class="w-3 h-3 rounded-full bg-cyan-400 animate-pulse shrink-0"></span>
          <span class="text-cyan-300 font-black tracking-widest text-lg uppercase whitespace-nowrap">{beat.caption_pill}</span>
        </div>
      </div>

    </div>

    <!-- RIGHT COLUMN (col-span-5, 45% width - "The Visual / Image Stage") -->
    <div class="col-span-5 flex flex-col justify-center items-center h-full relative z-20">
      
      <!-- Dedicated Framed Canvas -->
      <div class="w-full h-[760px] rounded-3xl bg-slate-900/60 border border-slate-700/80 p-6 flex flex-col justify-between shadow-2xl backdrop-blur-xl relative overflow-hidden">
        
        <!-- Header Bar: Small tag displaying beat.visual_title -->
        <div class="flex items-center justify-between pb-3 border-b border-slate-800/80 relative z-20 shrink-0">
          <div class="flex items-center space-x-2.5">
            <span class="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse"></span>
            <span class="text-sm font-mono font-bold text-slate-200 uppercase tracking-wider">{visual_title}</span>
          </div>
          <span class="text-[10px] font-mono text-cyan-300 font-bold uppercase tracking-widest px-2.5 py-0.5 bg-cyan-500/20 border border-cyan-400/30 rounded-md">
            {beat.visual_type.replace('_', ' ')}
          </span>
        </div>

        <!-- Center Graphic & Mascot Integration -->
        <div class="flex-1 flex flex-col justify-center min-h-0 relative z-10 w-full overflow-hidden">
          {right_visual_content}
        </div>

      </div>

    </div>

  </div>

</body>
</html>"""

    @classmethod
    async def render_beat_async(cls, beat: Beat, output_path: Union[str, Path]) -> str:
        """
        Renders a pristine 16:9 widescreen (1920x1080) slide PNG for a given beat with zero mascot collision.
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(viewport={"width": 1920, "height": 1080})
            html_content = cls._build_beat_page_html(beat)
            await page.set_content(html_content, wait_until="networkidle")
            await page.screenshot(path=str(output_file), type="png")
            await browser.close()

        return str(output_file)

    @classmethod
    async def render_beat_states_async(cls, beat: Beat, output_dir: Union[str, Path]) -> List[str]:
        """
        Renders pristine 16:9 widescreen slide for the beat and returns the frame path list.
        """
        out_dir_path = Path(output_dir)
        out_dir_path.mkdir(parents=True, exist_ok=True)
        frame_file = str(out_dir_path / f"beat_{beat.beat_id}.png")
        rendered_path = await cls.render_beat_async(beat, frame_file)
        return [rendered_path]

    @classmethod
    async def render_scene_phases_async(cls, scene, output_dir: Path) -> List[str]:
        """Legacy phase renderer alias for backward compatibility."""
        return await cls.render_beat_states_async(scene, output_dir)