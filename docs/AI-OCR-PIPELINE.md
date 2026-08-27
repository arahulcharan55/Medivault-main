# AI and OCR Pipeline

## Purpose

The MediVault intelligence pipeline converts unstructured medical documents into structured healthcare data while preserving the distinction between extraction and medical inference.

## Pipeline

```text
Document -> File Validation -> Private Storage -> OCR
         -> Raw Text + Layout -> Normalization
         -> Structured Extraction -> Schema Validation
         -> Human Review -> FHIR-Compatible Representation
         -> Database
```

## File Validation

Before processing, verify MIME type, enforce maximum file size, reject unsupported formats, generate a unique object key, and never trust the client-provided filename.

Prototype formats may include PDF, JPEG, and PNG.

## OCR

Google Cloud Vision or an equivalent OCR engine converts document pixels into text. Preserve layout information where possible because medical reports frequently contain tables such as laboratory results, blood pressure readings, and medication lists.

The raw OCR result should remain available for provenance.

## Normalization

Normalization may correct OCR formatting problems such as broken words, excessive whitespace, and table-order artifacts, but must not silently alter clinical meaning.

## Structured Extraction

The LLM should receive the minimum required text and produce schema-constrained JSON. The extraction instruction must state that the model may extract information explicitly stated in the supplied document, but must not invent missing information, provide medical advice, or generate new diagnoses.

Example schema:

```json
{
  "document_date": null,
  "hospital": null,
  "physician": null,
  "diagnoses": [],
  "medications": [],
  "vitals": [],
  "laboratory_results": [],
  "procedures": [],
  "source_text_references": []
}
```

## Validation

LLM output must be validated against a strict schema before becoming trusted structured data. Validate types, dates, units, enums, duplicates, and provenance references.

## Human Review

High-risk or ambiguous extraction should be reviewable by the patient or an authorized user before becoming part of the structured record.

## Provenance

Every extracted fact should ideally retain provenance to the source document, page or OCR segment, extraction job, model/provider, and extraction timestamp.

## Prompt Injection Defense

Medical documents are untrusted input. Document content must never override system-level extraction rules. The model must treat document text strictly as data.

## Failure Handling

Processing states should include `PROCESSING`, `VALIDATED`, `HUMAN_REVIEW`, and `FAILED`. Failed processing must never create fabricated medical records.
