"""
Job comparison module to identify new job postings.
"""
import json
import os
from typing import List, Dict
from datetime import datetime


def load_job_history(filepath: str) -> List[Dict]:
    """
    Load historical job data from JSON file.
    
    Args:
        filepath: Path to jobs history JSON file
        
    Returns:
        List of historical job dictionaries
    """
    if not os.path.exists(filepath):
        print(f"No history file found at {filepath}. Creating new history.")
        return []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except json.JSONDecodeError:
        print(f"Error reading JSON from {filepath}. Starting with empty history.")
        return []
    except Exception as e:
        print(f"Error loading job history: {str(e)}")
        return []


def save_job_history(jobs: List[Dict], filepath: str) -> None:
    """
    Save current jobs to history file.
    
    Args:
        jobs: List of job dictionaries to save
        filepath: Path to jobs history JSON file
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Add timestamp to each job
    for job in jobs:
        if "date_found" not in job:
            job["date_found"] = datetime.now().isoformat()
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(jobs, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(jobs)} jobs to history file")
    except Exception as e:
        print(f"Error saving job history: {str(e)}")


def find_new_jobs(current_jobs: List[Dict], historical_jobs: List[Dict]) -> List[Dict]:
    """
    Compare current jobs against historical jobs to find new ones.
    
    Jobs are considered the same if they have the same URL.
    
    Args:
        current_jobs: List of jobs from current scraping
        historical_jobs: List of jobs from previous runs
        
    Returns:
        List of new jobs not found in history
    """
    # Create a set of historical job URLs for fast lookup
    historical_urls = {job.get("url") for job in historical_jobs if job.get("url")}
    
    # Find jobs with URLs not in historical data
    new_jobs = []
    for job in current_jobs:
        job_url = job.get("url")
        if job_url and job_url not in historical_urls:
            new_jobs.append(job)
    
    print(f"Found {len(new_jobs)} new jobs out of {len(current_jobs)} total jobs")
    return new_jobs


def merge_jobs(current_jobs: List[Dict], historical_jobs: List[Dict]) -> List[Dict]:
    """
    Merge current jobs with historical jobs, avoiding duplicates.
    
    Args:
        current_jobs: List of jobs from current scraping
        historical_jobs: List of jobs from previous runs
        
    Returns:
        Merged list of all unique jobs
    """
    # Create a dictionary keyed by URL to avoid duplicates
    all_jobs_dict = {}
    
    # Add historical jobs first
    for job in historical_jobs:
        url = job.get("url")
        if url:
            all_jobs_dict[url] = job
    
    # Update with current jobs (this will update existing entries and add new ones)
    for job in current_jobs:
        url = job.get("url")
        if url:
            if url not in all_jobs_dict:
                # New job - add timestamp
                job["date_found"] = datetime.now().isoformat()
            all_jobs_dict[url] = job
    
    return list(all_jobs_dict.values())


def compare_and_update_jobs(current_jobs: List[Dict], history_filepath: str) -> List[Dict]:
    """
    Complete workflow: load history, find new jobs, and update history.
    
    Args:
        current_jobs: List of jobs from current scraping
        history_filepath: Path to jobs history JSON file
        
    Returns:
        List of new jobs found
    """
    # Load historical data
    historical_jobs = load_job_history(history_filepath)
    
    # Find new jobs
    new_jobs = find_new_jobs(current_jobs, historical_jobs)
    
    # Merge and save updated history
    merged_jobs = merge_jobs(current_jobs, historical_jobs)
    save_job_history(merged_jobs, history_filepath)
    
    return new_jobs
