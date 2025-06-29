from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import spacy
import numpy as np
import logging
import json

nlp = spacy.load("en_core_web_md")
logger = logging.getLogger(__name__)

# Initialize models (cache for performance)
tfidf_vectorizer = TfidfVectorizer(stop_words='english')
sbert_model = SentenceTransformer('all-MiniLM-L6-v2')

def calculate_similarity(job_desc, resumes, method='sbert'):
    """Calculate similarity scores using selected method"""
    if method == 'tfidf':
        vectors = tfidf_vectorizer.fit_transform([job_desc] + resumes)
        sim_matrix = cosine_similarity(vectors[0:1], vectors[1:])
        scores = sim_matrix[0]
    else:  # sBERT
        embeddings = sbert_model.encode([job_desc] + resumes)
        job_vector = embeddings[0:1]
        resume_vectors = embeddings[1:]
        scores = cosine_similarity(job_vector, resume_vectors)[0]
    
    # Convert to 0-100 scale
    return (scores * 100).round(2)

def extract_skills(text, skills_db):
    """Extract skills using predefined database"""
    doc = nlp(text.lower())
    found_skills = set()
    
    # Match with skills database
    for skill in skills_db:
        if skill.lower() in text.lower():
            found_skills.add(skill)
    
    # Extract entities
    for ent in doc.ents:
        if ent.label_ in ["SKILL", "TECH"] and len(ent.text.split()) < 4:
            found_skills.add(ent.text)
    
    return list(found_skills)

def analyze_resumes(job_desc, resumes_data, skills_db):
    """Full analysis pipeline"""
    resume_texts = [data['text'] for data in resumes_data]
    scores = calculate_similarity(job_desc, resume_texts, method='sbert')
    
    jd_skills = extract_skills(job_desc, skills_db)
    
    results = []
    for i, data in enumerate(resumes_data):
        resume_skills = extract_skills(data['text'], skills_db)
        missing_skills = set(jd_skills) - set(resume_skills)
        
        results.append({
            "file_name": data['file_name'],
            "candidate_name": data['candidate_name'],
            "contact": data['contact'],
            "score": float(scores[i]),
            "matched_skills": resume_skills,
            "missing_skills": list(missing_skills)
        })
    
    # Sort by score descending
    results.sort(key=lambda x: x['score'], reverse=True)
    
    # Generate summary stats
    top_missing = {}
    for res in results:
        for skill in res['missing_skills']:
            top_missing[skill] = top_missing.get(skill, 0) + 1
    
    summary = {
        "total_resumes": len(results),
        "average_score": float(np.mean(scores)),
        "top_missing_skills": sorted(top_missing.items(), key=lambda x: x[1], reverse=True)[:5]
    }
    
    return results, summary

def serialize_results(results, summary):
    """Serialize analysis results for storage"""
    return json.dumps({
        "summary": summary,
        "results": results
    })

def deserialize_results(json_str):
    """Deserialize stored results"""
    return json.loads(json_str)