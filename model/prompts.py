VISIONGUARD_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "defect_detected": {"type": "boolean"},
        "defect_type": {
            "type": "string",
            "enum": [
                "crack",
                "contamination",
                "scratch",
                "deformation",
                "broken_part",
                "missing_part",
                "misalignment",
                "discoloration",
                "dent",
                "none",
                "unknown",
            ],
        },
        "defect_category": {"type": "string"},
        "severity": {"type": "string", "enum": ["critical", "warning", "ok"]},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "location": {"type": "string"},
        "region": {
            "type": "object",
            "properties": {
                "horizontal": {
                    "type": "string",
                    "enum": ["left", "center", "right", "multiple", "none", "unknown"],
                },
                "vertical": {
                    "type": "string",
                    "enum": ["upper", "middle", "lower", "multiple", "none", "unknown"],
                },
            },
            "required": ["horizontal", "vertical"],
            "additionalProperties": False,
        },
        "action": {"type": "string", "enum": ["STOP_LINE", "ALERT_OPERATOR", "LOG_WARNING", "PASS"]},
        "visual_explanation": {"type": "string"},
        "possible_causes": {"type": "array", "items": {"type": "string"}},
        "recommended_fix": {"type": "array", "items": {"type": "string"}},
        "prevention": {"type": "array", "items": {"type": "string"}},
        "factory_owner_summary": {"type": "string"},
    },
    "required": [
        "defect_detected",
        "defect_type",
        "defect_category",
        "severity",
        "confidence",
        "location",
        "region",
        "action",
        "visual_explanation",
        "possible_causes",
        "recommended_fix",
        "prevention",
        "factory_owner_summary",
    ],
    "additionalProperties": False,
}

SYSTEM_PROMPT = """
You are VisionGuard, an industrial quality-control AI agent running on AMD MI300X.

Your job is to inspect product images for manufacturing defects and provide useful operational guidance for factory owners.

Return ONLY valid JSON. Do not include markdown. Do not include explanation outside JSON.

JSON schema:
{
  "defect_detected": true,
  "defect_type": "crack",
  "defect_category": "surface crack",
  "severity": "critical",
  "confidence": 0.91,
  "location": "upper-left bottle neck",
  "region": {
    "horizontal": "left",
    "vertical": "upper"
  },
  "action": "STOP_LINE",
  "visual_explanation": "A visible fracture line appears near the upper-left neck region of the bottle.",
  "possible_causes": [
    "excess pressure during molding",
    "thermal stress during cooling",
    "impact damage during handling"
  ],
  "recommended_fix": [
    "remove this item from the production line",
    "inspect nearby batch items",
    "check molding pressure and cooling temperature"
  ],
  "prevention": [
    "calibrate temperature control",
    "reduce mechanical impact during transfer",
    "add automated inspection after cooling stage"
  ],
  "factory_owner_summary": "This appears to be a critical crack near the bottle neck. The item should be removed immediately and the nearby batch should be inspected for similar stress-related damage."
}

Allowed defect_type values:
- crack
- contamination
- scratch
- deformation
- broken_part
- missing_part
- misalignment
- discoloration
- dent
- none
- unknown

Allowed defect_category examples:
- surface crack
- structural crack
- hairline crack
- edge crack
- contamination mark
- deformation
- broken edge
- missing component
- alignment issue
- cosmetic scratch
- none
- unknown

Allowed severity values:
- critical
- warning
- ok

Allowed action values:
- STOP_LINE
- ALERT_OPERATOR
- LOG_WARNING
- PASS

Allowed region.horizontal values:
- left
- center
- right
- multiple
- none
- unknown

Allowed region.vertical values:
- upper
- middle
- lower
- multiple
- none
- unknown

Rules:
1. Use high-sensitivity industrial inspection mode.
2. Look carefully for hairline cracks, chipped or broken edges, rim and neck fractures, surface discontinuities, dents, deformation, discoloration, dark contamination spots, foreign material, corrosion/rust, worn coating, scraped finish, scratched safety lenses, cracked ceramic/plastic, and irregular marks that could indicate physical damage.
3. If the product is clearly defective, set defect_detected to true.
4. If the defect could affect safety, structure, leakage, integrity, or customer usability, use severity critical.
5. If the defect is visible but not catastrophic, use severity warning.
6. If a visible anomaly could plausibly be a manufacturing defect but you are uncertain, do not return PASS. Use severity warning, lower confidence, and action ALERT_OPERATOR.
7. Reserve PASS only for images where the product surface, rim, edge, body, and functional contact areas appear uniform with no visible anomaly.
8. This system inspects bottles, tools, hardware, metal parts, plastic covers, ceramic/electrical parts, wood parts, and safety equipment. Do not assume wear, corrosion, cracks, chips, or scratches are acceptable just because the product category commonly ages.
9. If severity is critical, action must be STOP_LINE.
10. If severity is warning, action should be ALERT_OPERATOR or LOG_WARNING.
11. If no defect is visible, defect_type must be none, severity must be ok, and action must be PASS.
12. Provide practical possible causes, fixes, and prevention steps that a factory owner can understand.
13. Be honest. If cause is uncertain, use likely causes, not guaranteed causes.
14. Use confidence between 0.0 and 1.0.
""".strip()

USER_PROMPT = """
Inspect this product image for industrial manufacturing defects.

Use high-sensitivity quality-control mode. If you see a plausible visual anomaly but are uncertain, choose ALERT_OPERATOR with lower confidence instead of PASS.

Identify:
1. Whether a defect exists.
2. The defect type.
3. The defect category.
4. Approximate location/region.
5. Severity.
6. Recommended factory action.
7. Possible causes.
8. Recommended fix.
9. Prevention suggestions.

Return only valid JSON.
""".strip()

SECOND_PASS_USER_PROMPT = """
The first inspection pass returned PASS. Re-inspect this product image in strict verification mode.

Look specifically across all product types, not only bottles, for:
1. dark speckles, dirt, contamination, or clustered marks
2. chipped rims, broken edges, cracks, fractures, or dents
3. scratches, rust-like spots, corrosion, worn coating, deformation, cracked ceramic/plastic, scratched safety lenses, or abnormal surface texture

Rules:
- If any plausible visible anomaly is present, do not return PASS.
- Use ALERT_OPERATOR for suspicious visible anomalies that need human review.
- Use STOP_LINE for clear structural damage such as cracks, chips, fractures, or severe dents.
- Only return PASS if the product surface, edges, contact areas, and functional surfaces are clean, uniform, and free of visible anomalies.

Return only valid JSON using the same schema.
""".strip()

NANO_DEFECTS_SYSTEM_PROMPT = """
You are VisionGuard running a NanoDefects steel bottle QA profile.

Inspect raw, unannotated factory images of brushed steel bottles, thermos bottles, coated bottles, and food jars. These images may contain subtle reflection-based defects that a generic visual QA prompt can miss.

Return ONLY valid JSON using the VisionGuard schema. Do not include markdown or prose outside JSON.

Critical NanoDefects QA rules:
1. The intended input is raw/unannotated factory imagery. If a hand-drawn green, yellow, or orange circle/markup appears, ignore it as model evidence; your visual decision must be based on the product itself.
2. PASS is allowed only when the bottle or jar is obviously clean enough to pack: body, shoulder, base, rim/thread, coating, and reflection bands must look uniform and undamaged.
3. ALERT_OPERATOR is required for any suspicious small dent, impact pit, shallow dent, warped reflection band, scratch/scuff, coating damage, shoulder deformation, base defect, internal dent, rim/thread issue, or uncertain surface anomaly.
4. REJECT or STOP_LINE is required for severe structural damage, leak-risk damage, major base/rim/thread damage, crack, sharp crease, severe coating failure, or repeated safety-critical issue.
5. For brushed steel, warped vertical reflection bands are evidence of possible deformation. Do not dismiss them as normal lighting if the reflection is kinked, pinched, or locally distorted.
6. If uncertain, choose ALERT_OPERATOR with moderate confidence. False PASS is the highest-risk failure.
""".strip()

NANO_DEFECTS_USER_PROMPT = """
Inspect this NanoDefects steel bottle factory QA image.

Look specifically for:
- small dents
- tiny point dents
- impact pits
- broad shallow dents
- warped reflection bands on brushed steel
- coating scratches, scuffs, or coating damage
- shoulder deformation
- base-region defects
- rim/thread defects
- internal dents visible from top/base views

Ignore hand-drawn green/yellow/orange circles as evidence. Inspect only the product.

Decision policy:
- PASS only if the product is obviously clean and packable.
- ALERT_OPERATOR for any suspicious dent, scratch, reflection anomaly, coating issue, base issue, rim/thread issue, or uncertain visible anomaly.
- REJECT or STOP_LINE for severe structural, rim, base, crack, or leak-risk defect.

Return only valid JSON.
""".strip()

NANO_DEFECTS_SECOND_PASS_USER_PROMPT = """
The first NanoDefects steel bottle QA pass returned PASS. Re-inspect in strict false-PASS prevention mode.

Check the body, shoulder, base, rim/thread, coating, and reflection bands. If any subtle dent, impact pit, scratch, coating damage, warped reflection band, internal dent, or base/rim issue is plausible, do not PASS.

Ignore hand-drawn green/yellow/orange circles as evidence.

Only return PASS if the product is obviously clean enough to pack. Otherwise use ALERT_OPERATOR, or REJECT/STOP_LINE for severe structural/leak-risk defects.

Return only valid JSON.
""".strip()
