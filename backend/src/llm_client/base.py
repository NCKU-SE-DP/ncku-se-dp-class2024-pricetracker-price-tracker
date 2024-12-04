# backend/src/llm_client/base.py

import abc

from .exceptions import DomainMismatchException

from pydantic import BaseModel, Field


class MessagePassingInterfaceExample(BaseModel):
    key: str = Field(
        default=...,
        example="example",
        description="description"
    )
    

class LLMClientBase(metaclass=abc.ABCMeta):
    ...
    
    @abc.abstractmethod
    def func_a(...) -> ...:
        """
        Description
        """
        return NotImplemented
    
    @abc.abstractmethod
    def func_b(...) -> ...:
        """
        Description
        """
        return NotImplemented
    
    @staticmethod
    @abc.abstractmethod
    def func_c(...) -> ...:
        """
        Description
        """
        return NotImplemented
    
    @staticmethod
    def func_d(...) -> ...:
        """
        Description
        """
        return NotImplemented