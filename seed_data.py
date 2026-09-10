import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'factorymind.settings')
django.setup()

from accounts.models import CustomUser
from knowledge.models import Category, Tag, Document, DocumentChunk
from knowledge.services.ocr import generate_chunks, summarize_text
from knowledge.services.vector_store import rebuild_vector_index

def seed():
    print("Seeding FactoryMind AI initial data...")

    # 1. Create Default Roles & Superuser
    admin_user, created = CustomUser.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@factorymind.ai',
            'first_name': 'Chief',
            'last_name': 'Administrator',
            'role': CustomUser.Role.ADMIN,
            'department': 'Plant Engineering Management',
            'employee_id': 'EMP-0001',
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
        print(" -> Created Admin user (admin / admin123)")

    engineer_user, created = CustomUser.objects.get_or_create(
        username='engineer',
        defaults={
            'email': 'engineer@factorymind.ai',
            'first_name': 'Sarah',
            'last_name': 'Conner',
            'role': CustomUser.Role.ENGINEER,
            'department': 'Mechanical & Robotics Maintenance',
            'employee_id': 'EMP-1042',
        }
    )
    if created:
        engineer_user.set_password('engineer123')
        engineer_user.save()
        print(" -> Created Engineer user (engineer / engineer123)")

    tech_user, created = CustomUser.objects.get_or_create(
        username='technician',
        defaults={
            'email': 'tech@factorymind.ai',
            'first_name': 'Alex',
            'last_name': 'Rivera',
            'role': CustomUser.Role.TECHNICIAN,
            'department': 'Assembly Line 3 Operations',
            'employee_id': 'EMP-2088',
        }
    )
    if created:
        tech_user.set_password('tech123')
        tech_user.save()
        print(" -> Created Technician user (technician / tech123)")

    # 2. Categories
    categories = [
        ('Maintenance', 'Equipment preventive maintenance guides and repair standard operating procedures.', 'bi-tools'),
        ('Safety', 'OSHA & Industrial safety standards, hazard handling, and emergency protocols.', 'bi-shield-exclamation'),
        ('Troubleshooting', 'Diagnostic charts, error code lookup tables, and fault resolution routines.', 'bi-lightning-charge'),
        ('SOPs', 'Standard Operating Procedures for assembly lines, calibration, and quality control.', 'bi-clipboard-check'),
        ('Machine Manuals', 'Manufacturer original equipment manuals, wiring diagrams, and specifications.', 'bi-book'),
    ]

    cat_map = {}
    for name, desc, icon in categories:
        cat_obj, _ = Category.objects.get_or_create(name=name, defaults={'description': desc, 'icon_class': icon})
        cat_map[name] = cat_obj
    print(f" -> Created {len(cat_map)} categories")

    # 3. Tags
    tags = ['Hydraulics', 'High-Temp', 'Siemens PLC', 'Vibration', 'Electrical', 'Calibration', 'Robotics']
    tag_map = {}
    for t_name in tags:
        t_obj, _ = Tag.objects.get_or_create(name=t_name)
        tag_map[t_name] = t_obj
    print(f" -> Created {len(tag_map)} tags")

    # 4. Sample Industrial Documents
    sample_docs = [
        {
            'title': 'SOP-2024: Hydraulic Press High Pressure Motor Maintenance',
            'category': 'Maintenance',
            'file_type': Document.FileType.TXT,
            'tags': ['Hydraulics', 'High-Temp'],
            'text': (
                "STANDARD OPERATING PROCEDURE: HYDRAULIC PRESS MOTOR MAINTENANCE\n"
                "Document ID: SOP-2024-HYD\n"
                "Target Equipment: 500-Ton Hydraulic Press (Unit 4B)\n\n"
                "1. PRE-MAINTENANCE SAFETY PROTOCOL:\n"
                "- Perform Lockout/Tagout (LOTO) on Main Breaker Box 34A.\n"
                "- Verify system hydraulic pressure gauge reads 0 PSI before disassembling valve blocks.\n"
                "- Wear heat-resistant gloves and protective face shield.\n\n"
                "2. TROUBLESHOOTING MOTOR OVERHEATING (>85°C):\n"
                "- Inspect main intake oil filter for sludge accumulation. Replace filter element (Part #HF-992) if differential pressure exceeds 15 PSI.\n"
                "- Check pump coupling alignment. Misalignment exceeding 0.05 mm causes excess shaft bearing friction.\n"
                "- Replenish ISO VG 46 hydraulic oil level up to the sight glass mid-line.\n\n"
                "3. BEARING LUBRICATION PROCEDURE:\n"
                "- Inject 15 grams of Lithium-complex NLGI Grade 2 synthetic grease into high-speed bearings every 500 operational hours."
            )
        },
        {
            'title': 'ERR-9021: Siemens S7-1500 PLC Communication Fault Diagnostic Guide',
            'category': 'Troubleshooting',
            'file_type': Document.FileType.TXT,
            'tags': ['Siemens PLC', 'Electrical'],
            'text': (
                "INDUSTRIAL TROUBLESHOOTING GUIDE: SIEMENS S7-1500 PLC FAULTS\n"
                "Error Code: ERR-9021 (PROFINET Bus Failure / IO Device Offline)\n\n"
                "DIAGNOSTIC STEPS:\n"
                "1. Check the SF (System Fault) red LED status on CPU 1516-3 PN/DP.\n"
                "2. Verify RJ45 Ethernet connection integrity on Switch Port 4. Ensure Shielded Twisted Pair (STP) cable is grounded.\n"
                "3. Open TIA Portal V18 -> Diagnostic Buffer -> Read last hardware interrupt.\n"
                "4. Common Root Causes:\n"
                "   a) IP Address collision on subnet 192.168.1.x.\n"
                "   b) 24V DC Auxiliary Power Supply drop below 20.4V under high inductive solenoid load.\n"
                "   c) Damaged PROFINET connector clip causing intermittent packet loss.\n\n"
                "RECOVERY ACTION:\n"
                "Replace Ethernet cable patch cord, cycle power to ET 200MP remote I/O module, and trigger warm restart via CPU key switch."
            )
        },
        {
            'title': 'SAF-101: Emergency Chemical Spill & Lockout Tagout Standard',
            'category': 'Safety',
            'file_type': Document.FileType.TXT,
            'tags': ['Safety', 'High-Temp'],
            'text': (
                "FACTORY SAFETY MANUAL: EMERGENCY PROTOCOLS\n"
                "Document Reference: SAF-101-PLANT\n\n"
                "CHEMICAL SPILL CONTAINMENT PROTOCOL:\n"
                "1. Immediately evacuate non-essential personnel within a 20-meter radius of the spill zone.\n"
                "2. Retrieve the Chemical Spill Kit located at Bay C (contains absorbent pads, neutralizer powder, and nitrile suits).\n"
                "3. Apply neutralizer powder starting from the outer perimeter moving inward to prevent liquid spread.\n\n"
                "LOCKOUT / TAGOUT (LOTO) MANDATES:\n"
                "- No maintenance technician shall enter protective cages of Line 2 Robotic Arms without applying personal padlock to energy isolation switch ES-01."
            )
        }
    ]

    for item in sample_docs:
        doc, created = Document.objects.get_or_create(
            title=item['title'],
            defaults={
                'category': cat_map[item['category']],
                'file_type': item['file_type'],
                'uploaded_by': engineer_user,
                'extracted_text': item['text'],
                'summary': summarize_text(item['text']),
                'file_size': len(item['text'].encode('utf-8')),
                'page_count': 1,
                'is_ocr_processed': True,
                'is_indexed': True
            }
        )
        if created:
            for tag_name in item['tags']:
                if tag_name in tag_map:
                    doc.tags.add(tag_map[tag_name])
            
            # Generate Chunks
            page_map = [(1, item['text'])]
            chunks_data = generate_chunks(page_map)
            chunk_objs = [
                DocumentChunk(
                    document=doc,
                    chunk_index=c['index'],
                    content=c['content'],
                    page_number=c['page_number']
                ) for c in chunks_data
            ]
            DocumentChunk.objects.bulk_create(chunk_objs)
            print(f" -> Created sample document '{doc.title}' with {len(chunk_objs)} vector chunks.")

    # Rebuild Vector Index
    rebuild_vector_index()
    print("FactoryMind AI Seeding Complete!")

if __name__ == '__main__':
    seed()
