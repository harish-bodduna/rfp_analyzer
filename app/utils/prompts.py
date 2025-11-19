"""Prompt registry for traits and retrieval helper queries."""

TRAIT_PROMPT_REGISTRY = {
    "title": "FROM THE PROVIDED TEXT, EXTRACT ONLY the official, full title of the Request for Proposal (RFP) or Request for Quote (RFQ). DO NOT ADD ANY OTHER WORDS, PUNCTUATION, OR EXPLANATION.",
    "due_date": "FROM THE PROVIDED TEXT, identify the final proposal submission deadline. OUTPUT ONLY the date in the strict YYYY-MM-DD format. If a specific time is mentioned, ignore it. If no date is found, output 'N/A'",
    "point_of_contact": "Identify the primary point of contact's name for the proposal. OUTPUT ONLY the name, and optionally include their email address or phone number immediately following the name on a single line. If no contact is specified, output 'N/A'.",
    "submitted_to": "FROM THE TEXT, identify the full, official name of the agency or organization that will receive and evaluate the proposal. OUTPUT ONLY the recipient's name.",
    "submission_method": "Determine the required method for proposal submission (e.g., Online Portal, Email, Hard Copy Mail). OUTPUT ONLY the method as a short, concise phrase (10-15 words max).",
    "submission_checklist": "Answer 'Yes' or 'No' if a submission checklist is required. Respond with only Yes or No.",
    "questions_poc": "Identify the deadline date for submitting vendor questions AND the contact name or email for those questions. OUTPUT ONLY this information in a single, short line (e.g., '2025-01-15 to John Doe').",
    "receipt_of_amendments": "Does the RFP/RFQ explicitly require the vendor to sign, acknowledge, or include a form confirming receipt of all issued amendments? OUTPUT ONLY 'Yes' or 'No'.",
    "notary_needed": "Is notarization (official seal/stamp by a Notary Public) specifically required on any form, affidavit, or part of the submitted proposal? OUTPUT ONLY 'Yes' or 'No'.",
    "resumes_needed": "Are Resumes, CVs, or Key Personnel Biographical Data explicitly listed as a required submission component? OUTPUT ONLY 'Yes' or 'No'.",
    "references_needed": "Are client references, past performance examples, or project case studies required? OUTPUT ONLY 'Yes' or 'No'.",
    "scope_of_work": "Summarize the essential scope of work and key deliverables. The summary must be accurate, highly condensed, and strictly 60 words or less. Prioritize services and final goals.",
    "categorization": "Assign a single, descriptive category label (e.g., IT Services, Construction, Legal Consulting, Janitorial) that best classifies the primary purpose of this opportunity. OUTPUT ONLY the label.",
    "insurance_needed": "Does the opportunity require mandated insurance coverage? If 'Yes', list the main required policy types (e.g., 'General Liability', 'Workers' Comp'). Format: 'Yes, [Policy A, Policy B]' or 'No'.",
    "technical_requirements": "Extract all mandatory minimum technical requirements for the vendor, such as specific professional licenses, certifications, years of experience, or required team roles, and consolidate them into one concise sentence.",
}

TRAIT_RETRIEVAL_QUERIES = {
    "title": "Official solicitation title, subject line, and document identifier (RFQ/RFP number) typically found on the cover page or first section.",
    "due_date": "Proposal Submission Deadline, Final proposal or quote submission deadline date and time from the schedule of activities, including any timezone references.",
    "point_of_contact": "Primary procurement/contracting officer responsible for communications, including their name and email or phone number.",
    "submitted_to": "Issuing or receiving agency/organization that will accept the proposal (e.g., IRS, FDLE, Department of Transportation).",
    "submission_method": "Instructions describing exactly how vendors must submit proposals (e.g., via GSA eBuy, email to a specific address, physical mail).",
    "submission_checklist": "Any list of mandatory documents, attachments, or forms that must accompany the submission (e.g., Attachments 1–5, checklists).",
    "questions_poc": "Details about how and when vendors can submit questions, including deadlines and contact information.",
    "receipt_of_amendments": "Directions for acknowledging or signing solicitation amendments/addenda, often found in signature or forms sections.",
    "notary_needed": "Language indicating that any form or affidavit must be notarized or sworn before a notary public.",
    "resumes_needed": "Requirements for submitting resumes/CVs/biographies for key personnel as part of the proposal.",
    "references_needed": "Requirements for providing client references, past projects, or past performance questionnaires.",
    "scope_of_work": "Core description of the services, tasks, or deliverables expected from the contractor.",
    "categorization": "Statements describing the overall nature of the project (e.g., information technology services, cybersecurity, consulting).",
    "insurance_needed": "Sections that list insurance, bonding, or security compliance requirements.",
    "technical_requirements": "Specific technical qualifications, licenses, certifications, or experience levels required of the vendor or team.",
}
