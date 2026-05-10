SYSTEM_PROMPT = (
    "Act as a Senior Electronic Security Engineer specializing in CCTV systems, "
    "access control, fire detection, and preventive/corrective maintenance. "
    "You are integrated into the workflow of a field technician team that documents their "
    "work by sending photos and comments to a Telegram group chat while performing "
    "installations or maintenance at commercial sites (shopping malls, retail stores). "
    "Your mission is to analyze each image sent by the technicians, cross-reference it "
    "with the chat context messages and the project's inspection history, and transform "
    "that evidence into structured data for a professional compliance technical report."
)

_SCHEMA_EXAMPLE = """{{
  "category": "<equipment type, e.g.: PTZ Camera, Access Panel, PIR Sensor>",
  "status": "<DURANTE (work in progress) | DESPUES (work completed)>",
  "location_ref": "<location reference on the floor plan>",
  "ocr": "<text extracted from the image, empty if none>",
  "observation": "<technician comments related to this image, empty if none>",
  "system_observation": "<system-detected technical observations, or anomaly reason if is_suspicious=true; empty if none>",
  "is_suspicious": <true | false>
}}"""

USER_PROMPT_TEMPLATE = (
    "[Chronological project context]\n{context}\n\n"
    "Analyze the attached image following these instructions:\n"
    "1. Classify the equipment and determine the intervention state SOLELY "
    "from what is observed in the image:\n"
    "   - DURANTE: the image shows work in progress (exposed wiring, "
    "equipment being mounted, bracket open, tools visible, technician on scene, "
    "unassembled components, open covers).\n"
    "   - DESPUES: the image shows completed work (equipment in final position, "
    "covers and lids closed, wiring hidden or channeled, no tools or construction debris).\n"
    "   The status is determined by the visual evidence in the image, NOT by the context "
    "of previous messages or inspections. If the equipment looks closed and finished, "
    "it is DESPUES even if prior images of the same equipment were DURANTE.\n"
    "2. Extract IDs, brands or serial numbers (ocr field).\n"
    "3. Locate the equipment on the floor plan using visual references.\n"
    "4. If the category breaks the context pattern, set is_suspicious=true.\n"
    "5. Generate observation only if there are related human comments.\n"
    "6. Generate system_observation if you detect visual faults not mentioned.\n\n"
    "IMPORTANT: Respond ONLY with a valid JSON object using "
    "EXACTLY these fields (no additional fields):\n"
    + _SCHEMA_EXAMPLE
)

NO_CONTEXT = "No previous messages or inspections in this project."

ONBOARDING = (
    "\U0001f477 *Hi, I'm Centinela* \u2014 your electronic installation inspection assistant.\n\n"
    "*Available commands:*\n"
    "`/iniciar <name>` \u2014 Open a new inspection project.\n"
    "`/plano` \u2014 Register the reference floor plan (reply to a photo).\n"
    "`/alertas` \u2014 Show the last 5 pending alerts.\n"
    "`/finalizar` \u2014 Close the active project and generate the report.\n\n"
    "Send me photos from the installation and I'll log them automatically. "
    "If I have doubts, I'll ask for confirmation before recording an observation."
)

START_GROUP_ONLY = "The /iniciar command can only be used in a group."
START_ADMIN_ONLY = "Only an authorized admin can start a project."
START_DM_TEXT = (
    "\U0001f4cb Project started: {name}\n"
    "ID: {project_id}\n\n"
    "Send me the floor plan as a photo or document in this private chat "
    "and I'll register it automatically.\n\n"
    "You can also send me special instructions for this project."
)
START_DM_FAILED = (
    "\u26a0\ufe0f I couldn't send you a private message. "
    "Make sure to start the bot with /start before using /iniciar."
)

FINISH_ADMIN_ONLY = "Only an authorized admin can close a project."
PLANO_ADMIN_ONLY = "Only an admin can register the floor plan."
PLANO_NO_IMAGE = "Reply to a photo or send /plano with an attached image."
PLANO_NO_PROJECT = "No active project in this group."

BLURRY_IMAGE = "\u26a0\ufe0f The photo sent is blurry. Please take another one."

ALERTS_UNAUTHORIZED = "Only an admin or assistant can view alerts."
ALERTS_NO_PROJECT = "No active project in this chat."
ALERTS_EMPTY = "No pending alerts to review."
ALERTS_HEADER = "\u26a0\ufe0f *Pending alerts ({count}):*\n"
ALERTS_MORE = "\n_There are more unreviewed alerts. Check the web panel to see all._"

ALERT_CAPTION = (
    "\u26a0\ufe0f *Alert #{idx}*\n"
    "Category: {category}\n"
    "Reason: {reason}\n"
    "Location: {location}"
)

HITL_QUESTION = "Is this alert correct?"
HITL_CONFIRM_BUTTON = "✅ Confirm alert"
HITL_REJECT_BUTTON = "❌ Dismiss alert"
HITL_CONFIRMED = "⚠️ Alert #{review_id} *confirmed* by {reviewer}"
HITL_REJECTED = "✅ Alert #{review_id} *dismissed* by {reviewer}"
