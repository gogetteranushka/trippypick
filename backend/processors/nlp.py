import spacy
import re
from typing import List, Dict, Optional, Tuple
from collections import Counter
import logging

class NLPProcessor:
    def __init__(self, model_name: str = 'en_core_web_sm'):
        """Initialize NLP processor with spaCy model"""
        self.logger = logging.getLogger(__name__)
        
        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            self.logger.warning(f"Model {model_name} not found. Downloading...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", model_name])
            self.nlp = spacy.load(model_name)
            
        # Trip-related keywords for classification
        self.trip_keywords = {
            'adventure': ['trek', 'hike', 'climb', 'adventure', 'camping', 'rafting', 'expedition'],
            'leisure': ['relax', 'beach', 'resort', 'leisure', 'holiday', 'vacation'],
            'cultural': ['heritage', 'culture', 'temple', 'monument', 'history', 'museum'],
            'wellness': ['yoga', 'wellness', 'retreat', 'spa', 'meditation', 'ayurveda'],
            'wildlife': ['safari', 'wildlife', 'jungle', 'sanctuary', 'forest'],
            'spiritual': ['spiritual', 'pilgrimage', 'ashram', 'monastery'],
            'workation': ['workation', 'remote work', 'digital nomad', 'coworking']
        }
        
    def process_package_text(self, text: str) -> Dict:
        """Process package text and extract structured information"""
        doc = self.nlp(text)
        
        return {
            'entities': self._extract_entities(doc),
            'keywords': self._extract_keywords(doc),
            'trip_type': self._classify_trip_type(text),
            'locations': self._extract_locations(doc),
            'activities': self._extract_activities(text),
            'amenities': self._extract_amenities(text),
            'tags': self._generate_tags(text, doc)
        }
    
    def _extract_entities(self, doc) -> Dict[str, List[str]]:
        """Extract named entities from text"""
        entities = {
            'locations': [],
            'organizations': [],
            'dates': [],
            'money': [],
            'persons': []
        }
        
        for ent in doc.ents:
            if ent.label_ in ['GPE', 'LOC']:
                entities['locations'].append(ent.text)
            elif ent.label_ == 'ORG':
                entities['organizations'].append(ent.text)
            elif ent.label_ == 'DATE':
                entities['dates'].append(ent.text)
            elif ent.label_ == 'MONEY':
                entities['money'].append(ent.text)
            elif ent.label_ == 'PERSON':
                entities['persons'].append(ent.text)
        
        # Deduplicate
        for key in entities:
            entities[key] = list(set(entities[key]))
        
        return entities
    
    def _extract_keywords(self, doc, top_n: int = 10) -> List[str]:
        """Extract important keywords from text"""
        # Filter tokens
        keywords = []
        for token in doc:
            if (not token.is_stop and 
                not token.is_punct and 
                not token.is_space and
                token.pos_ in ['NOUN', 'PROPN', 'VERB'] and
                len(token.text) > 2):
                keywords.append(token.lemma_.lower())
        
        # Get most common keywords
        keyword_freq = Counter(keywords)
        return [word for word, _ in keyword_freq.most_common(top_n)]
    
    def _classify_trip_type(self, text: str) -> str:
        """Classify the type of trip based on content"""
        text_lower = text.lower()
        scores = {}
        
        for trip_type, keywords in self.trip_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                scores[trip_type] = score
        
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        
        return 'general'
    
    def _extract_locations(self, doc) -> List[str]:
        """Extract location names from text"""
        locations = []
        
        # From named entities
        for ent in doc.ents:
            if ent.label_ in ['GPE', 'LOC']:
                locations.append(ent.text)
        
        # Common location patterns
        location_patterns = [
            r'(?:visit|explore|trip to|tour of)\s+([A-Z][a-zA-Z\s]+)',
            r'([A-Z][a-zA-Z]+)\s+(?:trip|tour|package|getaway)',
        ]
        
        text = doc.text
        for pattern in location_patterns:
            matches = re.findall(pattern, text)
            locations.extend(matches)
        
        # Clean and deduplicate
        cleaned_locations = []
        for loc in locations:
            loc = loc.strip()
            if len(loc) > 2 and loc not in cleaned_locations:
                cleaned_locations.append(loc)
        
        return cleaned_locations
    
    def _extract_activities(self, text: str) -> List[str]:
        """Extract activities mentioned in the text"""
        activities = []
        
        # Activity keywords
        activity_verbs = [
            'trek', 'hike', 'climb', 'swim', 'dive', 'surf', 'ski',
            'raft', 'kayak', 'camp', 'explore', 'visit', 'tour',
            'ride', 'sail', 'fish', 'snorkel', 'paraglide'
        ]
        
        # Activity patterns
        patterns = [
            r'(?:go|will|can)\s+(\w+ing)',  # go trekking, will camping
            r'(\w+ing)\s+(?:in|at|on)',      # trekking in mountains
        ]
        
        text_lower = text.lower()
        
        # Find verb-based activities
        for verb in activity_verbs:
            if verb in text_lower:
                activities.append(verb + 'ing' if not verb.endswith('e') else verb[:-1] + 'ing')
        
        # Find pattern-based activities
        for pattern in patterns:
            matches = re.findall(pattern, text_lower)
            activities.extend(matches)
        
        # Clean and deduplicate
        return list(set(activity for activity in activities if len(activity) > 3))
    
    def _extract_amenities(self, text: str) -> List[str]:
        """Extract amenities and inclusions"""
        amenities = []
        
        amenity_keywords = [
            'accommodation', 'hotel', 'resort', 'homestay', 'camping',
            'meals', 'breakfast', 'lunch', 'dinner', 'food',
            'transport', 'transfer', 'pickup', 'drop',
            'guide', 'instructor', 'equipment', 'gear',
            'wifi', 'internet', 'parking', 'pool', 'spa'
        ]
        
        text_lower = text.lower()
        
        for amenity in amenity_keywords:
            if amenity in text_lower:
                amenities.append(amenity)
        
        return amenities
    
    def _generate_tags(self, text: str, doc) -> List[str]:
        """Generate relevant tags for the package"""
        tags = []
        
        # Add trip type
        trip_type = self._classify_trip_type(text)
        tags.append(trip_type)
        
        # Add locations
        locations = self._extract_locations(doc)
        tags.extend(locations[:3])  # Top 3 locations
        
        # Add activities
        activities = self._extract_activities(text)
        tags.extend(activities[:5])  # Top 5 activities
        
        # Add special tags
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['women only', 'ladies only', 'girls only']):
            tags.append('women-only')
        
        if any(word in text_lower for word in ['budget', 'backpack', 'cheap']):
            tags.append('budget-friendly')
        
        if any(word in text_lower for word in ['luxury', 'premium', '5 star']):
            tags.append('luxury')
        
        if any(word in text_lower for word in ['weekend', '2 days', '3 days']):
            tags.append('weekend-getaway')
        
        if any(word in text_lower for word in ['family', 'kids', 'children']):
            tags.append('family-friendly')
        
        # Clean and deduplicate
        cleaned_tags = []
        for tag in tags:
            tag = tag.lower().replace(' ', '-')
            if tag not in cleaned_tags and len(tag) > 2:
                cleaned_tags.append(tag)
        
        return cleaned_tags[:15]  # Return top 15 tags
    
    def extract_itinerary(self, text: str) -> List[Dict]:
        """Extract structured itinerary from text"""
        itinerary = []
        
        # Patterns for day-wise activities
        day_patterns = [
            r'Day\s*(\d+)[:\-\s]*(.+?)(?=Day\s*\d+|$)',
            r'(\d+)(?:st|nd|rd|th)\s*Day[:\-\s]*(.+?)(?=\d+(?:st|nd|rd|th)\s*Day|$)',
            r'D(\d+)[:\-\s]*(.+?)(?=D\d+|$)'
        ]
        
        for pattern in day_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                day_num = int(match.group(1))
                activities = match.group(2).strip()
                
                # Clean activities text
                activities = re.sub(r'\s+', ' ', activities)
                activities = activities.replace('\n', '. ')
                
                # Extract key points from activities
                doc = self.nlp(activities)
                key_activities = []
                
                for sent in doc.sents:
                    if len(sent.text.strip()) > 10:
                        key_activities.append(sent.text.strip())
                
                itinerary.append({
                    'day': day_num,
                    'title': f"Day {day_num}",
                    'activities': activities[:200],  # Limit length
                    'key_points': key_activities[:3]  # Top 3 points
                })
        
        return sorted(itinerary, key=lambda x: x['day'])
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two package descriptions"""
        doc1 = self.nlp(text1)
        doc2 = self.nlp(text2)
        
        return doc1.similarity(doc2)