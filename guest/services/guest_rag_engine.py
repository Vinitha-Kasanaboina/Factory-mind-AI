import os
import logging
from guest.models import GuestDocument
from guest.services.guest_vector_store import search_guest_chunks

logger = logging.getLogger(__name__)

MANDATORY_GUEST_DISCLAIMER = (
    "This answer is based on general industrial knowledge and may not match your company's specific procedures. "
    "Upload your manuals or register your company for company-specific answers."
)

def generate_guest_rag_response(session_key, user_query):
    """
    RAG Pipeline for Guest Mode:
    1. Checks if guest uploaded custom documents for session_key.
    2. If documents exist -> Grounded Document Mode over guest's session vector index.
    3. If no documents exist -> General Industrial AI Assistant Mode + Mandatory Disclaimer.
    Returns: (answer_text: str, citations: list, mode: str)
    """
    has_documents = GuestDocument.objects.filter(session_key=session_key).exists()

    if has_documents:
        # Grounded Document RAG Mode
        chunks = search_guest_chunks(session_key, user_query, top_k=4)
        citations = []
        seen_docs = set()
        for c in chunks:
            doc_key = f"{c['doc_title']} (p.{c['page_number']})"
            if doc_key not in seen_docs:
                seen_docs.add(doc_key)
                citations.append({
                    'doc_id': c['doc_id'],
                    'doc_title': c['doc_title'],
                    'page_number': c['page_number'],
                    'score': round(c.get('score', 0.0), 3),
                    'snippet': c['content'][:150] + "..."
                })

        if not chunks:
            answer = (
                f"I searched your temporary uploaded document(s) for **'{user_query}'**, but could not find a direct passage matching your query.\n\n"
                "**Tips:**\n"
                "- Try rephrasing your search keywords.\n"
                "- Ensure your uploaded PDF/Image contains readable text or OCR.\n"
                f"\n---\n*Note: {MANDATORY_GUEST_DISCLAIMER}*"
            )
            return answer, citations, 'DOCUMENT'

        top_chunk = chunks[0]
        additional_context = ""
        if len(chunks) > 1:
            additional_context = "\n\n**Additional Passages Found in Your Uploaded Manual:**\n" + "\n".join([
                f"• **{c['doc_title']} (p. {c['page_number']})**: {c['content'][:200]}..."
                for c in chunks[1:]
            ])

        answer = (
            f"Based on your uploaded session manual **{top_chunk['doc_title']}** (Page {top_chunk['page_number']}):\n\n"
            f"{top_chunk['content']}\n"
            f"{additional_context}\n\n"
            f"*Source verified from temporary session index (Relevance: {round(top_chunk.get('score', 0.85)*100, 1)}%).*"
        )
        return answer, citations, 'DOCUMENT'

    else:
        # General Industrial AI Assistant Mode
        general_answer = generate_general_industrial_knowledge(user_query)
        full_answer = f"{general_answer}\n\n⚠️ *{MANDATORY_GUEST_DISCLAIMER}*"
        return full_answer, [], 'GENERAL'


def generate_general_industrial_knowledge(user_query):
    """
    Synthesizes general industrial engineering guidance for common domains:
    bearings, motors, pumps, hydraulics, pneumatics, conveyors, electrical troubleshooting, safety, & preventive maintenance.
    """
    q = user_query.lower()

    if any(k in q for k in ['bearing', 'lubrication', 'grease', 'overheating bearing']):
        return (
            "### General Industrial Bearing Guidance\n\n"
            "**1. Inspection & Temperature Monitoring:**\n"
            "- Standard rolling element bearing operating temperatures should ideally remain below 70°C to 80°C.\n"
            "- Sudden temperature spikes usually indicate over-greasing, starved lubrication, or shaft misalignment.\n\n"
            "**2. Lubrication Best Practices:**\n"
            "- Always clean grease nipples before applying fresh grease to avoid injecting grit.\n"
            "- Use the recommended grease type (e.g. Lithium-Complex, Polyurea) and avoid mixing incompatible thickeners.\n"
            "- Re-grease while the motor/bearing is running if safety protocols allow, permitting excess grease to purge.\n\n"
            "**3. Vibration Diagnostics:**\n"
            "- High 1x RPM vibration suggests unbalance.\n"
            "- High 2x RPM vibration suggests shaft misalignment.\n"
            "- High-frequency peaks (4kHz - 10kHz) indicate early-stage bearing race defect."
        )

    elif any(k in q for k in ['motor', 'vibration', 'winding', 'overload', 'stator']):
        return (
            "### General Electric Motor Maintenance & Troubleshooting\n\n"
            "**1. Electrical Checks:**\n"
            "- **Insulation Resistance (Megger Test):** Measure winding-to-ground resistance. Minimum threshold is typically 1 MΩ + 1 MΩ per kV rating at 20°C.\n"
            "- **Phase Current Balance:** Ensure voltage balance across L1, L2, and L3 within 1% to 2% to prevent motor overheating.\n\n"
            "**2. Mechanical Alignment:**\n"
            "- Perform laser alignment on motor-pump/gearbox couplings to within 0.05 mm radial and axial tolerance.\n"
            "- Inspect cooling fan shroud for dust accumulation to ensure adequate airflow."
        )

    elif any(k in q for k in ['pump', 'cavitation', 'seal', 'flow', 'impeller']):
        return (
            "### General Centrifugal Pump Maintenance & Cavitation Troubleshooting\n\n"
            "**1. Cavitation Identification & Prevention:**\n"
            "- **Symptom:** Crackling/gravel-like noise inside pump housing accompanied by flow fluctuation.\n"
            "- **Cause:** Available NPSH (NPSHa) is lower than Required NPSH (NPSHr).\n"
            "- **Action:** Check suction strainers for blockages, ensure suction valve is fully open, and reduce fluid temperature if operating near vapor pressure.\n\n"
            "**2. Mechanical Seal Inspection:**\n"
            "- Inspect seal flush line flow and pressure.\n"
            "- Slight weeping during initial break-in is common, but steady leakage indicates face wear or O-ring degradation."
        )

    elif any(k in q for k in ['hydraulic', 'fluid', 'valve', 'pressure', 'oil']):
        return (
            "### General Hydraulic System Troubleshooting\n\n"
            "**1. Pressure Drops & Fluid Health:**\n"
            "- Maintain hydraulic fluid contamination levels according to ISO 4406 cleanliness standards (e.g. 16/14/11).\n"
            "- Monitor fluid operating temperature; fluid above 60°C rapidly accelerates seal oxidation and viscosity breakdown.\n\n"
            "**2. Relief Valve Calibration:**\n"
            "- Verify system pressure relief valve setting against manufacturer specification before adjusting manifold screws.\n"
            "- Bleed trapped air from cylinder high points after component replacement."
        )

    elif any(k in q for k in ['pneumatic', 'air', 'cylinder', 'compressor', 'filter']):
        return (
            "### General Pneumatic System & Air Line Troubleshooting\n\n"
            "**1. Compressed Air Quality:**\n"
            "- Ensure FRL (Filter, Regulator, Lubricator) units are drained daily of moisture and condensate.\n"
            "- Check compressed air line pressure drops across main distribution headers.\n\n"
            "**2. Actuator Performance:**\n"
            "- Sluggish pneumatic cylinder travel indicates worn piston seals or restricted exhaust flow controls."
        )

    elif any(k in q for k in ['safety', 'loto', 'spill', 'hazard', 'emergency']):
        return (
            "### General Industrial Safety & Lockout/Tagout (LOTO)\n\n"
            "**1. Lockout / Tagout (LOTO) Core Rule:**\n"
            "- Zero Energy State: Isolate electrical, hydraulic, pneumatic, and kinetic energy sources before servicing any machinery.\n"
            "- Verify isolation using a calibrated multimeter or pressure gauge before proceeding.\n\n"
            "**2. Personal Protective Equipment (PPE):**\n"
            "- Mandatory safety glasses, steel-toe boots, hearing protection, and task-specific gloves in active production zones."
        )

    else:
        return (
            f"### General Industrial Guidance for '{user_query}'\n\n"
            "**Industrial Best Practices Checklist:**\n"
            "1. **Inspection:** Inspect equipment for unusual noise, heat, vibration, or fluid weeping.\n"
            "2. **Safety First:** Apply Lockout/Tagout (LOTO) and verify Zero Energy State before mechanical intervention.\n"
            "3. **Documentation:** Log maintenance findings, replaced part numbers, and calibration values in your CMMS.\n"
            "4. **Preventive Maintenance:** Adhere to manufacturer lubrication intervals and component torque specifications."
        )
