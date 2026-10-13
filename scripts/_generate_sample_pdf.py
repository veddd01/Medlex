"""One-off script: generates data/sample_medical_book.pdf.

This is NOT part of the shipped application — it's a build-time helper so
the repo can include a small, clearly-labeled sample PDF for smoke-testing
`ingest.py` before you supply a real 700+ page medical encyclopedia. All
text below is written from scratch for this purpose (general, textbook-
level public-health information) — it is not copied from any encyclopedia
and is not a substitute for one.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

OUTPUT_PATH = "data/sample_medical_book.pdf"

ENTRIES = [
    ("The Common Cold", """
        The common cold is a mild viral infection of the nose and throat.
        More than 200 different viruses can cause a cold, most often
        rhinoviruses. Symptoms typically include a runny or stuffy nose,
        sneezing, a mild sore throat, coughing, and low energy, usually
        appearing one to three days after exposure and lasting about a
        week to ten days. Because colds are caused by viruses, antibiotics
        do not help; treatment focuses on rest, fluids, and managing
        symptoms until the immune system clears the infection. Washing
        hands regularly and avoiding close contact with sick individuals
        are the most effective ways to reduce the chance of catching or
        spreading a cold.
    """),
    ("Staying Hydrated", """
        Water makes up a large portion of the human body and is needed for
        regulating temperature, transporting nutrients, and removing waste.
        Daily fluid needs vary by body size, activity level, and climate,
        so there is no single number that fits everyone; a commonly used
        general guideline is to drink enough fluid that urine stays pale
        yellow throughout the day. Thirst, dry mouth, and dark urine are
        common early signs of mild dehydration. People who exercise
        heavily, spend time in hot weather, or are unwell with fever,
        vomiting, or diarrhea typically need more fluids than usual.
    """),
    ("Sleep and Health", """
        Sleep allows the brain and body to recover, consolidate memories,
        and regulate hormones involved in appetite, mood, and immune
        function. Most adults function best with roughly seven to nine
        hours of sleep per night, though individual needs vary. Consistent
        sleep and wake times, a dark and quiet sleeping environment, and
        limiting caffeine later in the day are commonly recommended habits
        for improving sleep quality. Ongoing sleep difficulty that affects
        daily functioning is worth discussing with a healthcare provider,
        since it can have several different underlying causes.
    """),
    ("Physical Activity Guidelines", """
        Regular physical activity supports cardiovascular health, muscle
        and bone strength, and mental well-being. General public health
        guidance for most adults suggests at least 150 minutes of
        moderate-intensity activity per week, such as brisk walking, along
        with muscle-strengthening activity on two or more days per week.
        Activity can be broken into shorter sessions throughout the day
        and still provide benefit. Anyone starting a new exercise routine
        with an existing health condition should check with a healthcare
        provider first.
    """),
    ("Handwashing and Infection Prevention", """
        Washing hands with soap and water for at least twenty seconds is
        one of the most effective ways to prevent the spread of infectious
        illness, including colds, flu, and many causes of stomach upset.
        Key times to wash hands include before eating, after using the
        restroom, and after coughing, sneezing, or blowing one's nose.
        When soap and water are not available, an alcohol-based hand
        sanitizer with at least 60 percent alcohol is a reasonable
        alternative, though it is less effective against some germs and
        does not work well on visibly dirty hands.
    """),
    ("Vaccination Basics", """
        Vaccines work by training the immune system to recognize a
        specific pathogen without causing the disease itself, so the body
        can respond quickly if it encounters the real infection later.
        Recommended vaccination schedules vary by age, health status, and
        country, and are typically set by national public health
        authorities based on ongoing safety and effectiveness data. Common
        mild side effects can include soreness at the injection site or a
        short-lived low fever. Anyone with questions about a specific
        vaccine or their own vaccination schedule should speak with a
        healthcare provider.
    """),
    ("Basic First Aid for Minor Cuts", """
        For a minor cut or scrape, first wash your hands, then rinse the
        wound gently with clean water to remove dirt or debris. Apply
        gentle pressure with a clean cloth or bandage until any light
        bleeding stops, then cover the area with a clean bandage and
        change it daily or whenever it becomes wet or dirty. Seek medical
        care for a wound that is deep, is bleeding heavily and will not
        stop, shows signs of infection such as increasing redness or
        pus, or resulted from a dirty or rusty object, since it may
        require stitches or a tetanus booster.
    """),
    ("Understanding Blood Pressure Readings", """
        Blood pressure is recorded as two numbers: systolic pressure (the
        higher number, measured when the heart beats) over diastolic
        pressure (the lower number, measured when the heart rests between
        beats). A commonly cited reference range for a healthy adult
        reading at rest is below 120 over 80 millimeters of mercury,
        though individual targets can vary based on age and health
        history. Blood pressure naturally fluctuates throughout the day,
        so a single elevated reading is not automatically a diagnosis;
        persistent high readings should be discussed with a healthcare
        provider.
    """),
]


def build_pdf() -> None:
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "EntryTitle", parent=styles["Heading1"], spaceAfter=12,
    )
    body_style = ParagraphStyle(
        "EntryBody", parent=styles["Normal"], leading=16, spaceAfter=6,
    )
    cover_style = ParagraphStyle(
        "Cover", parent=styles["Title"], spaceAfter=24,
    )
    disclaimer_style = ParagraphStyle(
        "Disclaimer", parent=styles["Italic"], textColor="#555555",
    )

    doc = SimpleDocTemplate(
        OUTPUT_PATH, pagesize=letter,
        topMargin=1 * inch, bottomMargin=1 * inch,
        leftMargin=1 * inch, rightMargin=1 * inch,
    )
    story = []

    story.append(Paragraph("Sample Health Reference (Demo Data)", cover_style))
    story.append(Paragraph(
        "This short document exists only to let you smoke-test "
        "ingest.py before pointing it at a real medical encyclopedia. "
        "It covers a handful of general, well-established public-health "
        "topics, written for this project rather than sourced from any "
        "encyclopedia. It is not medical advice and is not a substitute "
        "for a real reference text or a healthcare professional.",
        disclaimer_style,
    ))
    story.append(PageBreak())

    for i, (title, body) in enumerate(ENTRIES):
        story.append(Paragraph(title, title_style))
        story.append(Paragraph(" ".join(body.split()), body_style))
        if i < len(ENTRIES) - 1:
            story.append(PageBreak())

    doc.build(story)
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    build_pdf()
