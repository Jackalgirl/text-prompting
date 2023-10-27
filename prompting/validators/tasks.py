import torch
import textwrap
import random
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import List
from prompting.validators.criteria import TaskCriterion, MatchLengthCriteria, TextLengthUnitEnum

@dataclass
class Task(ABC):
    base_text: str    
    task_name: str
    task_type: str
    criteria: List[TaskCriterion] = field(default_factory=list)    

    @abstractmethod
    def compose_prompt(self) -> str:
        ...        

class SummaryTask(Task):    
    def compose_prompt(self) -> str:
        # Aggregates criteria in bullet points
        criteria_bullet_points = [f"- {criterion.compose_text()}" for criterion in self.criteria]
        criteria_bullet_points_str = "\n".join(criteria_bullet_points)

        prompt_template = textwrap.dedent("""\
        Your task is to summarize the text delimited with triple backticks:
        '''{base_text}'''
        
        The following criteria must be respected:
        {criteria}
        - Do not try to create questions or answers for your summarization. 
        """)

        prompt = prompt_template.format(base_text=self.base_text, criteria=criteria_bullet_points_str)        
        return prompt

class QuestionGenerationTask(Task):    
    def compose_prompt(self) -> str:
        # Aggregates criteria in bullet points
        criteria_bullet_points = [f"- {criterion.compose_text()}" for criterion in self.criteria]
        criteria_bullet_points_str = "\n".join(criteria_bullet_points)

        prompt_template = textwrap.dedent("""\
        Your task is to ask a single relevant and insightful question about the preceding context delimited with triple backticks:
        '''{base_text}'''
        
        The following criteria must be respected:
        {criteria}                                      
        - Do not answer the question you generate. 
        - Do not try to summarize the text
        """)

        prompt = prompt_template.format(base_text=self.base_text, criteria=criteria_bullet_points_str)        
        return prompt

class QuestionAnswerTask(Task):            
    def compose_prompt(self) -> str:
        # Aggregates criteria in bullet points
        criteria_bullet_points = [f"- {criterion.compose_text()}" for criterion in self.criteria]
        criteria_bullet_points_str = "\n".join(criteria_bullet_points)

        prompt_template = textwrap.dedent("""\
        Read the preceding context delimited with triple backticks carefully. Your task is to answer the question step by step and explain your thoughts:
        '''{base_text}'''
        
        The following criteria must be respected:
        {criteria}                                      
        - Do not include questions or summaries in your answer.
        """)

        prompt = prompt_template.format(base_text=self.base_text, criteria=criteria_bullet_points_str)        
        return prompt


def create_summarization_task(base_text: str) -> SummaryTask:
    match_words_criteria = MatchLengthCriteria(penalty=0.1, target_length=random.randint(50, 200), unit=TextLengthUnitEnum.WORDS),
    match_length_criteria = MatchLengthCriteria(penalty=0.1, target_length=random.randint(4, 8), unit=TextLengthUnitEnum.SENTENCES),
    
    criteria = [match_words_criteria, match_length_criteria]

    return SummaryTask(base_text=base_text, criteria=criteria, task_type='summarization', task_name='augment')

def create_qg_task(base_text: str, index: int) -> QuestionGenerationTask:
    match_words_criteria = MatchLengthCriteria(penalty=0.1, target_length=random.randint(25, 50), unit=TextLengthUnitEnum.WORDS),
    match_chars_criteria = MatchLengthCriteria(penalty=0.1, target_length=random.randint(125, 250), unit=TextLengthUnitEnum.CHARACTERS),
        
    criteria = [match_words_criteria, match_chars_criteria]

    return QuestionGenerationTask(base_text=base_text, criteria=criteria, task_type='question-generation', task_name=f'followup{index}')

def create_qa_task(base_text: str, index:int) -> QuestionAnswerTask:
    match_words_criteria = MatchLengthCriteria(penalty=0.1, target_length=random.randint(50, 200), unit=TextLengthUnitEnum.WORDS),
    match_length_criteria = MatchLengthCriteria(penalty=0.1, target_length=random.randint(4, 8), unit=TextLengthUnitEnum.SENTENCES)

    criteria = [match_words_criteria, match_length_criteria]

    return QuestionAnswerTask(base_text=base_text, criteria=criteria, task_type='question-answer', task_name=f'answer{index}')