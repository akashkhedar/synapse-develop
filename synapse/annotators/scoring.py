"""Scoring utilities for annotator tests"""


def calculate_iou(bbox1, bbox2):
    """Calculate Intersection over Union for bounding boxes"""
    x1 = max(bbox1['x'], bbox2['x'])
    y1 = max(bbox1['y'], bbox2['y'])
    x2 = min(bbox1['x'] + bbox1['width'], bbox2['x'] + bbox2['width'])
    y2 = min(bbox1['y'] + bbox1['height'], bbox2['y'] + bbox2['height'])
    
    if x2 < x1 or y2 < y1:
        return 0.0
    
    intersection = (x2 - x1) * (y2 - y1)
    area1 = bbox1['width'] * bbox1['height']
    area2 = bbox2['width'] * bbox2['height']
    union = area1 + area2 - intersection
    
    return intersection / union if union > 0 else 0.0


def score_ner_annotations(user_annotations, ground_truth, tolerance=5):
    """
    Score NER annotations using exact match with tolerance for start/end positions
    
    Args:
        user_annotations: List of {start, end, text, label}
        ground_truth: List of {start, end, text, label}
        tolerance: Allowed character difference for start/end positions
    
    Returns:
        tuple: (matched_count, precision, recall, f1_score)
    """
    true_positives = 0
    
    matched_gt = set()
    
    for user_ann in user_annotations:
        for i, gt_ann in enumerate(ground_truth):
            if i in matched_gt:
                continue
                
            # Check if labels match
            if user_ann['label'].upper() != gt_ann['label'].upper():
                continue
            
            # Check if positions overlap with tolerance
            start_diff = abs(user_ann['start'] - gt_ann['start'])
            end_diff = abs(user_ann['end'] - gt_ann['end'])
            
            if start_diff <= tolerance and end_diff <= tolerance:
                true_positives += 1
                matched_gt.add(i)
                break
    
    # Calculate metrics
    precision = true_positives / len(user_annotations) if user_annotations else 0
    recall = true_positives / len(ground_truth) if ground_truth else 0
    f1_score = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return true_positives, precision, recall, f1_score


def score_mcq(user_answer, correct_answer):
    """Score multiple choice question"""
    return user_answer == correct_answer


def score_classification(user_answer, correct_answer):
    """Score classification task"""
    return user_answer == correct_answer


def calculate_test_score(mcq_answers, text_annotations, classification_answers, test_data):
    """
    Calculate overall test score
    
    Args:
        mcq_answers: Dict of {question_id: answer_index}
        text_annotations: Dict of {task_id: [annotations]}
        classification_answers: Dict of {task_id: answer_index}
        test_data: Test questions and ground truth from test_data.py
    
    Returns:
        dict: Detailed scoring breakdown
    """
    knowledge_score = 0
    knowledge_total = 0
    
    # Score MCQ questions
    for question in test_data['knowledge_questions']:
        knowledge_total += question['points']
        user_answer = mcq_answers.get(question['id'])
        if user_answer is not None and score_mcq(user_answer, question['correct_answer']):
            knowledge_score += question['points']
    
    # Score text annotation tasks
    text_score = 0
    text_total = 0
    text_details = []
    
    for task in test_data['text_annotation_tasks']:
        text_total += task['points']
        user_anns = text_annotations.get(task['id'], [])
        
        matched, precision, recall, f1 = score_ner_annotations(
            user_anns,
            task['ground_truth']
        )
        
        # Score based on F1 score
        task_score = f1 * task['points']
        text_score += task_score
        
        text_details.append({
            'task_id': task['id'],
            'matched': matched,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'score': task_score,
            'max_score': task['points']
        })
    
    # Score classification tasks
    classification_score = 0
    classification_total = 0
    
    for task in test_data['classification_tasks']:
        classification_total += task['points']
        user_answer = classification_answers.get(task['id'])
        if user_answer is not None and score_classification(user_answer, task['correct_answer']):
            classification_score += task['points']
    
    # Calculate totals
    practical_score = text_score + classification_score
    practical_total = text_total + classification_total
    
    overall_score = knowledge_score + practical_score
    total_possible = knowledge_total + practical_total
    
    # Determine if passed
    scoring_config = test_data['scoring_config']
    percentage = (overall_score / total_possible * 100) if total_possible > 0 else 0
    
    passed = (
        overall_score >= scoring_config['pass_threshold'] and
        knowledge_score >= scoring_config['knowledge_min'] and
        practical_score >= scoring_config['practical_min']
    )
    
    return {
        'passed': passed,
        'overall_score': round(overall_score, 2),
        'total_possible': total_possible,
        'percentage': round(percentage, 2),
        'knowledge_score': knowledge_score,
        'knowledge_total': knowledge_total,
        'knowledge_percentage': round((knowledge_score / knowledge_total * 100) if knowledge_total > 0 else 0, 2),
        'text_score': round(text_score, 2),
        'text_total': text_total,
        'text_details': text_details,
        'classification_score': classification_score,
        'classification_total': classification_total,
        'practical_score': round(practical_score, 2),
        'practical_total': practical_total,
        'practical_percentage': round((practical_score / practical_total * 100) if practical_total > 0 else 0, 2),
    }





