import re
import logging
from pypdf import PdfReader
from datetime import datetime

LOG = logging.getLogger("abr_parsers")

def parse_date(date_str):
    """Parses ABR date format: 'DD Mon YYYY' (e.g. 05 Jan 2026) or 'None'."""
    if not date_str or date_str.lower() in ['none', '(current)', '']:
        return None
    try:
        # Expected format: 05 Jan 2026
        return datetime.strptime(date_str.strip(), "%d %b %Y").date()
    except ValueError:
        # Try a more relaxed parse if needed
        LOG.debug(f"Failed to parse date: {date_str}")
        return None

def normalize_history_row(row, source_doc_id):
    """Normalizes a history row with From/To dates and is_current flag."""
    from_date = parse_date(row.get('from'))
    to_text = row.get('to', '').strip().lower()
    
    is_current = '(current)' in to_text or not to_text or to_text == 'none'
    to_date = None if is_current else parse_date(to_text)
    
    return {
        'from_date': from_date,
        'to_date': to_date,
        'is_current': is_current,
        'source_document_id': source_doc_id
    }

class ABRPDFParser:
    def __init__(self, filepath, source_doc_id):
        self.filepath = filepath
        self.source_doc_id = source_doc_id
        self.text = self._extract_text()
        self.doc_type = self._identify_type()

    def _extract_text(self):
        reader = PdfReader(self.filepath)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text

    def _identify_type(self):
        if "Current details for ABN" in self.text:
            return "CURRENT"
        elif "Historical details for ABN" in self.text:
            return "HISTORICAL"
        else:
            raise ValueError("Unknown ABR PDF type")

    def parse(self):
        if self.doc_type == "CURRENT":
            return self._parse_current()
        else:
            return self._parse_historical()

    def _find_value(self, label, text=None):
        if text is None: text = self.text
        # Handles "Label: Value" or "Label Value"
        pattern = rf"{label}\s*[:]?\s*(.*)"
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).split('\n')[0].strip() if match else None

    def _get_section(self, header, next_headers):
        """Extracts text between a header and the next header in the PDF text."""
        start = self.text.find(header)
        if start == -1: return ""
        
        end = len(self.text)
        for h in next_headers:
            pos = self.text.find(h, start + len(header))
            if pos != -1 and pos < end:
                end = pos
        return self.text[start + len(header):end].strip()

    def _parse_current(self):
        data = {
            'entity': {},
            'name_history': [],
            'status_history': [],
            'location_history': [],
            'business_names': [],
            'trading_names': [],
            'gst_history': [],
            'asic_registration': []
        }
        
        # Header info
        abn_match = re.search(r"Current details for ABN\s*(\d{2}\s*\d{3}\s*\d{3}\s*\d{3})", self.text)
        abn = abn_match.group(1).replace(" ", "") if abn_match else None
        
        record_extracted = self._find_value("Record extracted")
        abn_updated = self._find_value("ABN last updated")
        
        # Entity section
        entity_name = self._find_value("Entity name")
        abn_status_val = self._find_value("ABN status")
        active_from = None
        if abn_status_val and "Active from" in abn_status_val:
            active_from = abn_status_val.split("Active from")[-1].strip()
        
        entity_type = self._find_value("Entity type")
        
        data['entity'] = {
            'abn': abn,
            'entity_name': entity_name,
            'entity_type': entity_type,
            'first_active_date': parse_date(active_from),
            'abn_last_updated_date': parse_date(abn_updated),
            'record_extracted_date': parse_date(record_extracted),
            'source_document_id': self.source_doc_id
        }

        headers = ["Entity name", "ABN status", "Entity type", "Goods & Services Tax (GST)", 
                   "Main business location", "Business name(s)", "Trading name(s)", "ASIC registration", "Record extracted"]

        # Name History (current name)
        data['name_history'].append({
            'abn': abn,
            'entity_name': entity_name,
            'from_date': parse_date(active_from),
            'to_date': None,
            'is_current': True,
            'source_document_id': self.source_doc_id
        })

        # Status History
        data['status_history'].append({
            'abn': abn,
            'status': 'Active' if 'Active' in (abn_status_val or "") else abn_status_val,
            'from_date': parse_date(active_from),
            'to_date': None,
            'is_current': True,
            'source_document_id': self.source_doc_id
        })

        # Location
        location_text = self._get_section("Main business location", headers)
        loc_match = re.search(r"([A-Z]{2,3})\s*(\d{4})", location_text)
        if loc_match:
            data['location_history'].append({
                'abn': abn,
                'state': loc_match.group(1),
                'postcode': loc_match.group(2),
                'from_date': parse_date(active_from),
                'to_date': None,
                'is_current': True,
                'source_document_id': self.source_doc_id
            })

        # GST
        gst_text = self._get_section("Goods & Services Tax (GST)", headers)
        if gst_text and "Not registered" not in gst_text:
            lines = gst_text.split('\n')
            for line in lines:
                if "Registered from" in line:
                    status = line.split("Registered from")[0].strip() or "Registered"
                    registered_from = line.split("Registered from")[-1].strip()
                    data['gst_history'].append({
                        'abn': abn,
                        'gst_status': status,
                        'from_date': parse_date(registered_from),
                        'to_date': None,
                        'is_current': True,
                        'source_document_id': self.source_doc_id
                    })

        # Business Names
        bn_text = self._get_section("Business name(s)", headers)
        if bn_text and "No business names" not in bn_text:
            for line in bn_text.split('\n'):
                match = re.search(r"(.*)\s+(\d{2}\s+[A-Z][a-z]{2}\s+\d{4})", line)
                if match:
                    data['business_names'].append({
                        'abn': abn,
                        'business_name': match.group(1).strip(),
                        'from_date': parse_date(match.group(2)),
                        'source_document_id': self.source_doc_id
                    })

        # Trading Names
        tn_text = self._get_section("Trading name(s)", headers)
        if tn_text and "No trading names" not in tn_text:
            for line in tn_text.split('\n'):
                match = re.search(r"(.*)\s+(\d{2}\s+[A-Z][a-z]{2}\s+\d{4})", line)
                if match:
                    data['trading_names'].append({
                        'abn': abn,
                        'trading_name': match.group(1).strip(),
                        'from_date': parse_date(match.group(2)),
                        'source_document_id': self.source_doc_id
                    })

        return data

    def _parse_historical(self):
        data = {
            'entity': {},
            'name_history': [],
            'status_history': [],
            'location_history': [],
            'gst_history': [],
            'asic_registration': [],
            'business_names': [],
            'trading_names': []
        }
        
        abn_match = re.search(r"Historical details for ABN\s*(\d{2}\s*\d{3}\s*\d{3}\s*\d{3})", self.text)
        abn = abn_match.group(1).replace(" ", "") if abn_match else None
        
        record_extracted = self._find_value("Record extracted")
        abn_updated = self._find_value("ABN last updated")
        entity_type = self._find_value("Entity type")

        # Actual PDF section headers (not "history" suffix - actual format has "From To" in header)
        # Sections: "Entity name From To", "ABN Status From To", "Main business location From To", 
        # "Good & Services Tax (GST) From To", "Trading name(s)", etc.
        headers = [
            "Entity name", "ABN Status", "Entity type", "Main business location", 
            "Good & Services Tax (GST)", "Goods & Services Tax (GST)",  # Both spellings
            "Trading name(s)", "Business name(s)", "ASIC registration", 
            "Record extracted", "Disclaimer", "Warning Statement"
        ]

        # Entity Name History - section starts with "Entity name From To"
        name_section = self._get_section("Entity name", headers)
        first_entity_name = None
        for line in name_section.split('\n'):
            # Skip header line that contains 'From To'
            if 'From To' in line or not line.strip():
                continue
            # Pattern: NAME DD Mon YYYY (current) or NAME DD Mon YYYY DD Mon YYYY
            match = re.search(r"^(.+?)\s+(\d{2}\s+[A-Z][a-z]{2}\s+\d{4})\s*(.*)?$", line.strip())
            if match:
                name = match.group(1).strip()
                from_date = match.group(2)
                to_part = match.group(3).strip() if match.group(3) else ""
                
                if not first_entity_name:
                    first_entity_name = name
                
                row = normalize_history_row({'from': from_date, 'to': to_part}, self.source_doc_id)
                row.update({'abn': abn, 'entity_name': name})
                data['name_history'].append(row)

        # ABN Status History - section starts with "ABN Status From To"
        status_section = self._get_section("ABN Status", headers)
        earliest_active_date = None
        for line in status_section.split('\n'):
            if 'From To' in line or not line.strip():
                continue
            match = re.search(r"^(.+?)\s+(\d{2}\s+[A-Z][a-z]{2}\s+\d{4})\s*(.*)?$", line.strip())
            if match:
                status = match.group(1).strip()
                from_date = match.group(2)
                to_part = match.group(3).strip() if match.group(3) else ""
                
                row = normalize_history_row({'from': from_date, 'to': to_part}, self.source_doc_id)
                row.update({'abn': abn, 'status': status})
                data['status_history'].append(row)
                
                # Track earliest active date
                if status.lower() == 'active' and row['from_date']:
                    if not earliest_active_date or row['from_date'] < earliest_active_date:
                        earliest_active_date = row['from_date']

        # Main Business Location History - section starts with "Main business location From To"
        loc_section = self._get_section("Main business location", headers)
        for line in loc_section.split('\n'):
            if 'From To' in line or not line.strip():
                continue
            # Pattern: STATE POSTCODE DD Mon YYYY (current) or STATE POSTCODE DD Mon YYYY DD Mon YYYY
            match = re.search(r"^([A-Z]{2,3})\s+(\d{4})\s+(\d{2}\s+[A-Z][a-z]{2}\s+\d{4})\s*(.*)?$", line.strip())
            if match:
                state = match.group(1)
                postcode = match.group(2)
                from_date = match.group(3)
                to_part = match.group(4).strip() if match.group(4) else ""
                
                row = normalize_history_row({'from': from_date, 'to': to_part}, self.source_doc_id)
                row.update({'abn': abn, 'state': state, 'postcode': postcode})
                data['location_history'].append(row)

        # GST History - may be "Good & Services Tax" or "Goods & Services Tax"
        gst_section = self._get_section("Good & Services Tax (GST)", headers)
        if not gst_section:
            gst_section = self._get_section("Goods & Services Tax (GST)", headers)
        if gst_section and "No current or historical GST" not in gst_section:
            for line in gst_section.split('\n'):
                if 'From To' in line or not line.strip():
                    continue
                match = re.search(r"^(.+?)\s+(\d{2}\s+[A-Z][a-z]{2}\s+\d{4})\s*(.*)?$", line.strip())
                if match:
                    gst_status = match.group(1).strip()
                    from_date = match.group(2)
                    to_part = match.group(3).strip() if match.group(3) else ""
                    
                    row = normalize_history_row({'from': from_date, 'to': to_part}, self.source_doc_id)
                    row.update({'abn': abn, 'gst_status': gst_status})
                    data['gst_history'].append(row)

        # Trading Names
        tn_section = self._get_section("Trading name(s)", headers)
        if tn_section and "stopped collecting" not in tn_section:
            for line in tn_section.split('\n'):
                if 'From To' in line or not line.strip() or 'ABR stopped' in line or 'business name' in line.lower():
                    continue
                match = re.search(r"^(.+?)\s+(\d{2}\s+[A-Z][a-z]{2}\s+\d{4})\s*(.*)?$", line.strip())
                if match:
                    row = normalize_history_row({'from': match.group(2), 'to': match.group(3) or ""}, self.source_doc_id)
                    row.update({'abn': abn, 'trading_name': match.group(1).strip()})
                    data['trading_names'].append(row)

        # ASIC Registration
        asic_section = self._get_section("ASIC registration", headers)
        if asic_section:
            match = re.search(r"([A-Z]{3})\s+([\d\s]+)", asic_section)
            if match:
                data['asic_registration'].append({
                    'abn': abn,
                    'asic_number': match.group(2).replace(" ", ""),
                    'asic_type': match.group(1),
                    'source_document_id': self.source_doc_id
                })

        # Build entity record
        data['entity'] = {
            'abn': abn,
            'entity_name': first_entity_name,
            'entity_type': entity_type,
            'first_active_date': earliest_active_date,
            'abn_last_updated_date': parse_date(abn_updated),
            'record_extracted_date': parse_date(record_extracted),
            'source_document_id': self.source_doc_id
        }

        return data

if __name__ == "__main__":
    import sys
    import json
    if len(sys.argv) > 1:
        logging.basicConfig(level=logging.INFO)
        parser = ABRPDFParser(sys.argv[1], "test-uuid")
        print(json.dumps(parser.parse(), indent=2, default=str))
