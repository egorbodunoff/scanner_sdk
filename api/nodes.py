import os
from ctypes import *
import logging

from exceptions.camera_exceptions import NodeInitializationError, NodeValueError

logger = logging.getLogger(__name__)

class BaseNode:
    """
    Базовый дескриптор для узлов камеры.
    """
    def __init__(self, node_attr):
        self.node_attr = node_attr
        logger.info(f"Initialized BaseNode for attribute {self.node_attr}")

    def __get__(self, instance, owner):
        node = getattr(instance, self.node_attr)
        return self._get_node_value(node)

    def __set__(self, instance, value):
        node = getattr(instance, self.node_attr)
        self._set_node_value(node, value)
        logger.info(f"Set value {value} for node {self.node_attr}")

    def _get_node_value(self, node):
        if node is None:
            logger.error(f"Node {self.node_attr} is not initialized")
            raise NodeInitializationError(self.node_attr)
        
        value = self._get_value_type()()
        nRet = node.contents.getValue(node, byref(value))              
        if nRet != 0:
            logger.error(f"Failed to get value for node {self.node_attr}")
            raise NodeValueError(self.node_attr)
        
        logger.info(f"Successfully retrieved value {value.value} for node {self.node_attr}")
        return value.value

    def _set_node_value(self, node, value):
        if node is None:
            logger.error(f"Node {self.node_attr} is not initialized")
            raise NodeInitializationError(self.node_attr)
        
        nRet = node.contents.setValue(node, self._get_value_type()(value))
        if nRet != 0:
            logger.error(f"Failed to set value {value} for node {self.node_attr}")
            raise NodeValueError(self.node_attr, value)
        
        logger.info(f"Successfully set value {value} for node {self.node_attr}")
        return True
    
    def _get_min_max_values(self, node):
        value_type = self._get_value_type()
        
        min_value = value_type()
        nRet = node.contents.getMinVal(node, byref(min_value))              
        if nRet != 0:
            logger.warning(f'Failed to get minimum value for {self.__class__.__name__}.')
            print(f'Failed to get minimum value for {self.__class__.__name__}.')
        else:
            self.min_value = min_value.value 

        max_value = value_type()
        nRet = node.contents.getMaxVal(node, byref(max_value))              
        if nRet != 0:
            logger.warning(f'Failed to get maximum value for {self.__class__.__name__}.')
            print(f'Failed to get maximum value for {self.__class__.__name__}.')
        else:
            self.max_value = max_value.value 

    def _get_value_type(self):
        raise NotImplementedError

class IntNode(BaseNode):
    """
    Дескриптор для узлов типа int.
    """
    def __init__(self, node_attr):
        super().__init__(node_attr)

        self.min_value = None
        self.max_value = None

    def __set__(self, instance, value):
        if not isinstance(value, int):
            logger.error(f"Value must be a int, got {type(value).__name__}")
            raise TypeError(f'Value must be an integer, got {type(value).__name__}')
        
        if self.min_value is not None and value < self.min_value:
            logger.error(f"Value {value} is below the minimum allowed value of {self.min_value}")
            raise ValueError(f'Value {value} is below the minimum allowed value of {self.min_value}')
        
        if self.max_value is not None and value > self.max_value:
            logger.error(f"Value {value} is above the maximum allowed value of {self.max_value}")
            raise ValueError(f'Value {value} is above the maximum allowed value of {self.max_value}')
        
        super().__set__(instance, value)

    def _get_value_type(self):
        return c_long
    
    def _get_node_value(self, node):
        self._get_min_max_values(node)
        
        return super()._get_node_value(node)


class DoubleNode(BaseNode):
    """
    Дескриптор для узлов типа double.
    """
    def __init__(self, node_attr):
        super().__init__(node_attr)

        self.min_value = None
        self.max_value = None

    def __set__(self, instance, value):
        if not isinstance(value, (int, float)):
            logger.error(f"Value must be a number, got {type(value).__name__}")
            raise TypeError(f'Value must be a number, got {type(value).__name__}')
        
        if self.min_value is not None and value < self.min_value:
            logger.error(f"Value {value} is below the minimum allowed value of {self.min_value}")
            raise ValueError(f'Value {value} is below the minimum allowed value of {self.min_value}')
        
        if self.max_value is not None and value > self.max_value:
            logger.error(f"Value {value} is above the maximum allowed value of {self.max_value}")
            raise ValueError(f'Value {value} is above the maximum allowed value of {self.max_value}')
        
        super().__set__(instance, value)

    def _get_value_type(self):
        return c_double
    
    def _get_node_value(self, node):
        self._get_min_max_values(node)
        
        return super()._get_node_value(node)


class EnumNode(BaseNode):
    """
    Дескриптор для узлов типа enum.
    """
    def __init__(self, node_attr, allowed_values=None):
        super().__init__(node_attr)
        self.allowed_values = allowed_values

    def __set__(self, instance, value):
        if value is not None and value not in self.allowed_values:
            logger.error(f"Value {value} is not in the allowed values {self.allowed_values}")
            raise ValueError(f'Value {value} is not in the allowed values {self.allowed_values}')
        super().__set__(instance, value)

    def _get_value_type(self):
        return c_ulong
    

class BoolNode(BaseNode):
    """
    Дескриптор для узлов типа boolean.
    """
    def __init__(self, node_attr):
        super().__init__(node_attr)

    def __set__(self, instance, value):
        if value is not None and value not in (0, 1):
            logger.error(f"Value {value} is not in the allowed values {(0, 1)}")
            raise ValueError(f'Value {value} is not in the allowed values {(0, 1)}')
        super().__set__(instance, value)

    def _get_value_type(self):
        return c_uint
