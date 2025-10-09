# -*- coding: utf-8 -*-
# created by mmmy on 2025-09-27

import logging
from ai.agent import ExtractPeopleAgent
from utils import ocr, vsdb, obs
from models.people import People
from fastapi import FastAPI

api = FastAPI(title="Single People Management and Searching", version="1.0.0")

class App:
    def __init__(self):
        self.extract_people_agent = ExtractPeopleAgent()
        self.ocr = ocr.get_instance()
        self.vedb = vsdb.get_instance(db_type='chromadb')
        self.obs = obs.get_instance()

    def run(self):
        pass
    
    class InputForPeople:
        image: bytes
        text: str
        
    def input_to_people(self, input: InputForPeople) -> People:
        if not input.image and not input.text:
            return None
        if input.image:
            content = self.ocr.recognize_image_text(input.image)
        else:
            content = input.text
        print(content)
        people = self._trans_text_to_people(content)
        return people
    
    def _trans_text_to_people(self, text: str) -> People:
        if not text:
            return None
        person = self.extract_people_agent.extract_people_info(text)
        print(person)
        return person
    
    def create_people(self, people: People) -> bool:
        if not people:
            return False
        try:
            people.save()
        except Exception as e:
            logging.error(f"保存人物到数据库失败: {e}")
            return False
        return True