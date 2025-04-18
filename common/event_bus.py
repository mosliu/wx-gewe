from typing import Callable, Dict, List
from common.log import logger

class EventBus:
    _subscribers: Dict[str, List[Callable]] = {}

    @classmethod
    def subscribe(cls, event: str, callback: Callable) -> None:
        """订阅事件"""
        if event not in cls._subscribers:
            cls._subscribers[event] = []
        cls._subscribers[event].append(callback)
        logger.debug(f"[EventBus] Subscribed to event: {event}")

    @classmethod
    def publish(cls, event: str, *args, **kwargs) -> None:
        """发布事件"""
        if event in cls._subscribers:
            for callback in cls._subscribers[event]:
                try:
                    callback(*args, **kwargs)
                except Exception as e:
                    logger.error_with_trace(
                        f"Error in event handler for {event}: {str(e)}"
                    )
        logger.debug(f"[EventBus] Published event: {event}")