from __future__ import annotations

from pathlib import Path

from pawagent.models.analysis import UnifiedAnalysisResult
from pawagent.models.media import ImageInput
from pawagent.providers.base import BaseProvider


class MockProvider(BaseProvider):
    def analyze_image(self, image: ImageInput, prompt: str) -> dict[str, object]:
        del prompt
        stem = image.path.stem.lower()
        observed_species = self._infer_species(stem)

        if any(keyword in stem for keyword in ("play", "happy", "park", "run")):
            return {
                "species": self._species_payload(requested_species="", observed_species=observed_species),
                "emotion": {
                    "label": "playful",
                    "confidence": 0.91,
                    "arousal": "high",
                    "tags": ["excited", "engaged"],
                    "alternatives": ["excited"],
                    "evidence": ["open posture", "active stance"],
                    "uncertainty_note": "Could also read as excitement because the body is highly activated.",
                },
                "behavior": {
                    "label": "seeking interaction",
                    "confidence": 0.86,
                    "target": "human",
                    "intensity": "high",
                    "evidence": ["active stance", "engaged focus"],
                    "alternatives": ["playing"],
                    "uncertainty_note": "Single image limits certainty about sustained play.",
                    "notes": "Open posture and active engagement cues.",
                },
                "motivation": {
                    "label": "seeking engagement",
                    "confidence": 0.81,
                    "alternatives": ["wants play", "wants attention"],
                    "evidence": ["open posture", "active stance", "engaged focus"],
                    "uncertainty_note": "Single frame limits certainty about the exact interaction goal.",
                },
                "expression": {
                    "plain_text": "The pet appears playful and is actively seeking interaction.",
                    "pet_voice": "I want to play with you right now.",
                    "tone": "eager",
                    "grounded_in": ["open posture", "active stance", "engaged focus"],
                    "confidence": 0.78,
                },
                "evidence": ["open posture", "active stance", "engaged focus"],
            }
        if any(keyword in stem for keyword in ("sleep", "nap", "rest", "calm")):
            return {
                "species": self._species_payload(requested_species="", observed_species=observed_species),
                "emotion": {
                    "label": "relaxed",
                    "confidence": 0.88,
                    "arousal": "low",
                    "tags": ["calm", "sleepy"],
                    "alternatives": ["tired"],
                    "evidence": ["settled posture", "soft expression"],
                    "uncertainty_note": "Without motion, tiredness and relaxation can overlap.",
                },
                "behavior": {
                    "label": "resting",
                    "confidence": 0.85,
                    "target": "self",
                    "intensity": "low",
                    "evidence": ["low activity", "settled body posture"],
                    "alternatives": ["settling"],
                    "uncertainty_note": "Static posture suggests rest but not duration.",
                    "notes": "Low activity and settled body posture.",
                },
                "motivation": {
                    "label": "wants rest",
                    "confidence": 0.79,
                    "alternatives": ["wants low stimulation"],
                    "evidence": ["settled posture", "low activity", "soft expression"],
                    "uncertainty_note": "Single image cannot confirm whether the rest is brief or prolonged.",
                },
                "expression": {
                    "plain_text": "The pet appears comfortable and is likely resting.",
                    "pet_voice": "I feel comfortable and want to rest.",
                    "tone": "calm",
                    "grounded_in": ["settled posture", "low activity", "soft expression"],
                    "confidence": 0.8,
                },
                "evidence": ["settled posture", "low activity", "soft expression"],
            }
        if any(keyword in stem for keyword in ("alert", "bark", "guard")):
            return {
                "species": self._species_payload(requested_species="", observed_species=observed_species),
                "emotion": {
                    "label": "alert",
                    "confidence": 0.84,
                    "arousal": "medium",
                    "tags": ["focused"],
                    "alternatives": ["curious"],
                    "evidence": ["forward attention", "focused gaze"],
                    "uncertainty_note": "Could also be mild curiosity because no overt stress signal is visible.",
                },
                "behavior": {
                    "label": "monitoring surroundings",
                    "confidence": 0.81,
                    "target": "environment",
                    "intensity": "moderate",
                    "evidence": ["still stance", "forward attention"],
                    "alternatives": ["observing"],
                    "uncertainty_note": "Single-frame evidence cannot confirm how long the vigilance lasts.",
                    "notes": "Attentive posture directed outward.",
                },
                "motivation": {
                    "label": "monitoring for change",
                    "confidence": 0.74,
                    "alternatives": ["anticipating interaction", "checking environment"],
                    "evidence": ["forward attention", "still stance", "focused gaze"],
                    "uncertainty_note": "The trigger for vigilance is not visible in this frame.",
                },
                "expression": {
                    "plain_text": "The pet appears alert and is monitoring the surroundings.",
                    "pet_voice": "I am watching everything carefully right now.",
                    "tone": "watchful",
                    "grounded_in": ["forward attention", "still stance", "focused gaze"],
                    "confidence": 0.74,
                },
                "evidence": ["forward attention", "still stance", "focused gaze"],
            }

        return {
            "species": self._species_payload(requested_species="", observed_species=observed_species),
            "emotion": {
                "label": "curious",
                "confidence": 0.76,
                "arousal": "medium",
                "tags": ["observant"],
                "alternatives": ["alert"],
                "evidence": ["head orientation", "steady gaze"],
                "uncertainty_note": "Curiosity and alertness can overlap in single-image analysis.",
            },
            "behavior": {
                "label": "observing",
                "confidence": 0.72,
                "target": "environment",
                "intensity": "moderate",
                "evidence": ["steady gaze", "measured posture"],
                "alternatives": ["exploring"],
                "uncertainty_note": "Static evidence limits stronger motion-based interpretation.",
                "notes": "Investigative but not highly aroused.",
            },
            "motivation": {
                "label": "understanding the environment",
                "confidence": 0.69,
                "alternatives": ["checking novelty"],
                "evidence": ["head orientation", "steady gaze", "measured posture"],
                "uncertainty_note": "Observation alone cannot confirm whether the next action will be approach or pause.",
            },
            "expression": {
                "plain_text": "The pet appears curious and is observing the environment.",
                "pet_voice": "I am figuring out what is happening here.",
                "tone": "curious",
                "grounded_in": ["head orientation", "steady gaze", "measured posture"],
                "confidence": 0.69,
            },
            "evidence": ["head orientation", "steady gaze", "measured posture"],
        }

    def analyze_audio(self, audio_path: str, prompt: str) -> dict[str, object]:
        del prompt
        stem = Path(audio_path).stem.lower()
        if any(keyword in stem for keyword in ("bark", "woof", "alarm")):
            return {
                "species": self._species_payload(requested_species="", observed_species="dog"),
                "emotion": {"label": "alert", "confidence": 0.86, "tags": ["vocal", "focused"]},
                "behavior": {
                    "label": "signaling",
                    "confidence": 0.83,
                    "target": "environment",
                    "notes": "Vocal output suggests active alerting.",
                },
                "motivation": {
                    "label": "drawing attention to a stimulus",
                    "confidence": 0.76,
                    "alternatives": ["alerting others"],
                    "evidence": ["repeated sharp vocalization"],
                    "uncertainty_note": "Audio alone does not reveal the exact external trigger.",
                },
                "expression": {
                    "plain_text": "The pet sounds alert and is likely signaling about something in the environment.",
                    "pet_voice": "Something needs attention right now.",
                    "tone": "urgent",
                    "grounded_in": ["repeated sharp vocalization"],
                    "confidence": 0.76,
                },
                "evidence": ["repeated sharp vocalization"],
            }
        if any(keyword in stem for keyword in ("purr", "hum", "calm")):
            return {
                "species": self._species_payload(requested_species="", observed_species="cat"),
                "emotion": {"label": "relaxed", "confidence": 0.87, "tags": ["soothing", "steady"]},
                "behavior": {
                    "label": "settling",
                    "confidence": 0.82,
                    "target": "self",
                    "notes": "Steady low-arousal vocalization.",
                },
                "motivation": {
                    "label": "maintaining comfort",
                    "confidence": 0.73,
                    "alternatives": ["seeking calm contact"],
                    "evidence": ["soft continuous sound"],
                    "uncertainty_note": "Audio alone limits broader environmental interpretation.",
                },
                "expression": {
                    "plain_text": "The pet sounds calm and appears to be settled.",
                    "pet_voice": "I feel calm and comfortable.",
                    "tone": "calm",
                    "grounded_in": ["soft continuous sound"],
                    "confidence": 0.79,
                },
                "evidence": ["soft continuous sound"],
            }
        return {
            "species": self._species_payload(requested_species="", observed_species="other"),
            "emotion": {"label": "curious", "confidence": 0.74, "tags": ["attentive"]},
            "behavior": {
                "label": "listening",
                "confidence": 0.71,
                "target": "environment",
                "notes": "Audio suggests attentive engagement rather than rest.",
            },
            "motivation": {
                "label": "checking the environment",
                "confidence": 0.67,
                "alternatives": ["seeking more information"],
                "evidence": ["variable attentive vocalization"],
                "uncertainty_note": "Without visual context, the source of attention is unclear.",
            },
            "expression": {
                "plain_text": "The pet sounds attentive and is likely checking what is happening.",
                "pet_voice": "I am listening and checking what is happening.",
                "tone": "attentive",
                "grounded_in": ["variable attentive vocalization"],
                "confidence": 0.67,
            },
            "evidence": ["variable attentive vocalization"],
        }

    def analyze_video(self, video_path: str, prompt: str) -> dict[str, object]:
        del prompt
        stem = Path(video_path).stem.lower()
        observed_species = self._infer_species(stem)
        if any(keyword in stem for keyword in ("run", "zoom", "play")):
            return {
                "species": self._species_payload(requested_species="", observed_species=observed_species),
                "emotion": {"label": "excited", "confidence": 0.89, "tags": ["active", "engaged"]},
                "behavior": {
                    "label": "playing",
                    "confidence": 0.88,
                    "target": "human",
                    "notes": "Sustained active movement suggests play.",
                },
                "motivation": {
                    "label": "releasing energy through play",
                    "confidence": 0.82,
                    "alternatives": ["seeking interactive play"],
                    "evidence": ["repeated fast movement", "engaged motion pattern"],
                    "uncertainty_note": "Video suggests play, but the exact social target may still vary.",
                },
                "expression": {
                    "plain_text": "The pet appears excited and is actively playing.",
                    "pet_voice": "I have a lot of energy and want to keep moving.",
                    "tone": "energetic",
                    "grounded_in": ["repeated fast movement", "engaged motion pattern"],
                    "confidence": 0.8,
                },
                "evidence": ["repeated fast movement", "engaged motion pattern"],
            }
        if any(keyword in stem for keyword in ("hide", "avoid", "retreat")):
            return {
                "species": self._species_payload(requested_species="", observed_species=observed_species),
                "emotion": {"label": "anxious", "confidence": 0.83, "tags": ["withdrawn", "guarded"]},
                "behavior": {
                    "label": "avoiding",
                    "confidence": 0.84,
                    "target": "environment",
                    "notes": "Movement pattern indicates withdrawal or retreat.",
                },
                "motivation": {
                    "label": "creating distance from a perceived stressor",
                    "confidence": 0.77,
                    "alternatives": ["avoiding interaction"],
                    "evidence": ["repeated retreat", "distance-seeking movement"],
                    "uncertainty_note": "Video shows avoidance, but not the exact cause of the stress.",
                },
                "expression": {
                    "plain_text": "The pet appears uneasy and is trying to create distance.",
                    "pet_voice": "I want distance and do not feel fully at ease.",
                    "tone": "guarded",
                    "grounded_in": ["repeated retreat", "distance-seeking movement"],
                    "confidence": 0.73,
                },
                "evidence": ["repeated retreat", "distance-seeking movement"],
            }
        return {
            "species": self._species_payload(requested_species="", observed_species=observed_species),
            "emotion": {"label": "curious", "confidence": 0.78, "tags": ["engaged"]},
            "behavior": {
                "label": "exploring",
                "confidence": 0.79,
                "target": "environment",
                "notes": "Movement pattern suggests investigation.",
            },
            "motivation": {
                "label": "exploring novelty",
                "confidence": 0.71,
                "alternatives": ["surveying the environment"],
                "evidence": ["investigative movement pattern"],
                "uncertainty_note": "Exploration is inferred from movement pattern rather than explicit object interaction.",
            },
            "expression": {
                "plain_text": "The pet appears curious and is actively exploring.",
                "pet_voice": "I am exploring and figuring things out.",
                "tone": "curious",
                "grounded_in": ["investigative movement pattern"],
                "confidence": 0.7,
            },
            "evidence": ["investigative movement pattern"],
        }

    def render_expression(
        self,
        analysis: UnifiedAnalysisResult,
        locale: str,
        style: str = "default",
    ) -> dict[str, object]:
        normalized = locale.strip() or "en"
        if normalized.lower().startswith("en"):
            return analysis.expression.model_dump(mode="json")

        emotion_map = {
            "playful": "开心想玩",
            "relaxed": "放松",
            "alert": "警觉",
            "curious": "好奇",
            "excited": "兴奋",
            "anxious": "紧张",
        }
        behavior_map = {
            "seeking interaction": "正在主动寻求互动",
            "resting": "正在休息",
            "monitoring surroundings": "在留意周围环境",
            "observing": "在观察周围",
            "playing": "在玩耍",
            "avoiding": "在回避",
            "exploring": "在探索",
        }
        motivation_map = {
            "seeking engagement": "我想和你互动一下",
            "wants rest": "我想安静休息",
            "monitoring for change": "我想先确认周围有没有变化",
            "understanding the environment": "我想先弄清楚现在发生了什么",
            "releasing energy through play": "我想继续跑动和玩耍",
            "creating distance from a perceived stressor": "我想离让自己不舒服的东西远一点",
            "exploring novelty": "我想看看这里有没有新东西",
        }

        if normalized.lower().startswith("zh"):
            emotion_text = emotion_map.get(analysis.emotion.primary, analysis.emotion.primary)
            behavior_text = behavior_map.get(analysis.behavior.label, analysis.behavior.label)
            pet_voice = motivation_map.get(analysis.motivation.label, analysis.expression.pet_voice)
            return {
                "plain_text": f"宠物看起来比较{emotion_text}，并且{behavior_text}。",
                "pet_voice": pet_voice,
                "tone": analysis.expression.tone,
                "grounded_in": analysis.expression.grounded_in,
                "confidence": analysis.expression.confidence,
                "locale": normalized,
                "source_language": "en",
                "style": style,
            }

        return {
            "plain_text": analysis.expression.plain_text,
            "pet_voice": analysis.expression.pet_voice,
            "tone": analysis.expression.tone,
            "grounded_in": analysis.expression.grounded_in,
            "confidence": analysis.expression.confidence,
            "locale": normalized,
            "source_language": "en",
            "style": style,
        }

    def _infer_species(self, stem: str) -> str:
        if any(keyword in stem for keyword in ("dog", "woof", "bark", "milo")):
            return "dog"
        if any(keyword in stem for keyword in ("cat", "meow", "purr", "luna", "tuna", "coconut")):
            return "cat"
        return "other"

    def _species_payload(self, requested_species: str, observed_species: str) -> dict[str, object]:
        requested = requested_species.strip().lower()
        mismatch = ""
        if requested and requested not in {"unknown", "other"} and requested != observed_species:
            mismatch = f"Requested species '{requested}' does not match observed species '{observed_species}'."
        return {
            "requested_species": requested,
            "observed_species": observed_species,
            "confidence": 0.92 if observed_species in {"dog", "cat"} else 0.62,
            "used_framework": observed_species if observed_species in {"dog", "cat"} else "other",
            "mismatch_warning": mismatch,
        }
